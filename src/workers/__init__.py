from PyQt5.QtCore import QObject, pyqtSignal

class Worker(QObject):
    """Worker class for running operations in a separate thread"""
    started = pyqtSignal()
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)
    progress = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.work = None
    
    def run(self):
        """Run the worker's task"""
        try:
            self.started.emit()
            result = self.work()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)
            
    def update_progress(self, value: int):
        """Update progress value"""
        self.progress.emit(value)

def create_thread_worker(function, *args, **kwargs):
    """Create a new worker thread for the given function"""
    thread = QThread()
    worker = Worker()
    worker.work = lambda: function(*args, **kwargs)
    worker.moveToThread(thread)
    
    # Connect thread start to worker run
    thread.started.connect(worker.run)
    # Clean up thread when finished
    worker.finished.connect(thread.quit)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker

def cleanup_thread(thread, worker):
    """Clean up thread and worker properly"""
    if thread and thread.isRunning():
        thread.quit()
        thread.wait()  # Wait for thread to finish
