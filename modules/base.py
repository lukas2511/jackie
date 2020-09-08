class Object(object):
    def __init__(self):
        self.running = True
        self.run()
        self.threads.append(self)

    def stop(self):
        self.running = False
        if hasattr(self, "thread") and self.thread.is_alive():
            self.process.terminate()
            self.thread.join()
