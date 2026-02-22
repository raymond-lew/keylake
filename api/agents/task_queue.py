"""SQLite-based Task Queue for AI CRM Agents

This module provides a simple task queue using SQLite instead of Redis/Celery.
Tasks are stored in the database and executed by a background worker thread.
"""

import sqlite3
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
from contextlib import contextmanager
import traceback

DATABASE_PATH = "tasks.db"


@contextmanager
def get_db_connection():
    """Get database connection with proper context management"""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the task queue database"""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                args TEXT DEFAULT '[]',
                kwargs TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                result TEXT,
                error TEXT,
                retries INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status 
            ON tasks(status, scheduled_at)
        """)
        conn.commit()


class TaskQueue:
    """SQLite-based task queue with worker thread"""
    
    def __init__(self):
        self.tasks: Dict[str, Callable] = {}
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
        self.poll_interval = 2.0  # seconds
        
    def register_task(self, name: str, func: Callable):
        """Register a task function"""
        self.tasks[name] = func
        
    def enqueue(self, task_name: str, args: list = None, kwargs: dict = None, 
                delay_seconds: int = 0, max_retries: int = 3) -> int:
        """Add a task to the queue"""
        scheduled_at = datetime.now() + timedelta(seconds=delay_seconds)
        
        with get_db_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO tasks (task_name, args, kwargs, scheduled_at, max_retries)
                VALUES (?, ?, ?, ?, ?)
            """, (task_name, json.dumps(args or []), json.dumps(kwargs or {}), 
                  scheduled_at.isoformat(), max_retries))
            conn.commit()
            return cursor.lastrowid
    
    def get_pending_tasks(self, limit: int = 10) -> List[sqlite3.Row]:
        """Get pending tasks that are ready to execute"""
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM tasks 
                WHERE status = 'pending' AND scheduled_at <= ?
                ORDER BY scheduled_at ASC
                LIMIT ?
            """, (datetime.now().isoformat(), limit))
            return cursor.fetchall()
    
    def update_task_status(self, task_id: int, status: str, 
                          result: Any = None, error: str = None):
        """Update task status"""
        with get_db_connection() as conn:
            if status == 'running':
                conn.execute("""
                    UPDATE tasks SET status = ?, started_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, task_id))
            elif status == 'completed':
                conn.execute("""
                    UPDATE tasks SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, json.dumps(result) if result else None, task_id))
            elif status == 'failed':
                conn.execute("""
                    UPDATE tasks SET status = ?, error = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, error, task_id))
            elif status == 'retry':
                conn.execute("""
                    UPDATE tasks SET status = 'pending', retries = retries + 1,
                    scheduled_at = datetime(CURRENT_TIMESTAMP, '+60 seconds')
                    WHERE id = ?
                """, (task_id,))
            conn.commit()
    
    def execute_task(self, task: sqlite3.Row):
        """Execute a single task"""
        task_name = task['task_name']
        task_id = task['id']
        
        if task_name not in self.tasks:
            self.update_task_status(task_id, 'failed', 
                                   error=f"Unknown task: {task_name}")
            return
        
        try:
            self.update_task_status(task_id, 'running')
            
            args = json.loads(task['args'])
            kwargs = json.loads(task['kwargs'])
            
            func = self.tasks[task_name]
            result = func(*args, **kwargs)
            
            self.update_task_status(task_id, 'completed', result=result)
            print(f"✅ Task {task_id} ({task_name}) completed")
            
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            retries = task['retries']
            max_retries = task['max_retries']
            
            if retries < max_retries:
                print(f"⚠️ Task {task_id} ({task_name}) failed, retrying... ({retries + 1}/{max_retries})")
                self.update_task_status(task_id, 'retry')
            else:
                print(f"❌ Task {task_id} ({task_name}) failed permanently: {error_msg}")
                self.update_task_status(task_id, 'failed', error=error_msg)
    
    def worker_loop(self):
        """Main worker loop"""
        print("🔄 Task worker started")
        while self.running:
            try:
                tasks = self.get_pending_tasks()
                for task in tasks:
                    if not self.running:
                        break
                    self.execute_task(task)
            except Exception as e:
                print(f"Worker error: {e}")
            
            time.sleep(self.poll_interval)
        
        print("Task worker stopped")
    
    def start(self):
        """Start the worker thread"""
        init_db()
        self.running = True
        self.worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker_thread.start()
        print("🚀 Task queue initialized (SQLite-based)")
    
    def stop(self):
        """Stop the worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with get_db_connection() as conn:
            stats = {}
            for status in ['pending', 'running', 'completed', 'failed']:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE status = ?", (status,))
                stats[status] = cursor.fetchone()[0]
            return stats


# Global task queue instance
task_queue = TaskQueue()


def task(func):
    """Decorator to register a function as a task"""
    task_name = func.__name__
    task_queue.register_task(task_name, func)
    
    def wrapper(*args, **kwargs):
        # For compatibility with Celery-style calls
        return task_queue.enqueue(task_name, list(args), kwargs)
    
    wrapper.delay = wrapper
    wrapper.apply_async = wrapper
    return wrapper


def init_task_queue():
    """Initialize and start the task queue"""
    task_queue.start()
    return task_queue
