class CurationLogger:
    
    #initialize the logger to write to whatever file name is inputted
    def __init__(self, file_name):
        self.file=open(file_name, "w")
        self.step_num = 1

    def log(self, message):
        self.file.write(f"\n\t {message}")

    def step(self, step, description=""):
        self.file.write(f"\nStep {self.step_num} : {step}.  {description}")
        self.step_num = self.step_num + 1

    def change(self, column_name, before, after):
        self.file.write(f"\n\tColumn {column_name} change:\tBefore: {before} \tAfter: {after}")
    
    def error(self, column_name, error):
        self.file.write(f"\n\tColumn {column_name} error: {error}")
    
    def close(self):
        self.file.close()

        