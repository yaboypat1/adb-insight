from PyQt5.QtCore import QObject, pyqtSignal, QThread

class Worker(QObject):
    """Worker class for running operations in a separate thread"""
    
    finished = pyqtSignal()  # Signal when the operation is complete
    error = pyqtSignal(str)  # Signal when an error occurs
    result = pyqtSignal(object)  # Signal to return the result
    
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.thread = None  # Store thread reference
        
    def run(self):
        """Execute the worker function"""
        try:
            result = self.function(*self.args, **self.kwargs)
            self.result.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

def create_thread_worker(function, *args, **kwargs):
    """Create a new worker thread for the given function"""
    thread = QThread()
    worker = Worker(function, *args, **kwargs)
    worker.thread = thread  # Store thread reference
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
