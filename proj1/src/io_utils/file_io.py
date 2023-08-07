class FileIO:
    def read_lines(file_path):
        lines = []
        try:
            lines = open(file_path, "r").read().splitlines()
        except FileNotFoundError:
            return False, f"file with file_path '{file_path}' not found"
        except IOError:
            return False, f"IO error when reading file with file_path '{file_path}'"
        return True, lines
    
    def write_lines(file_path, lines):
        try: 
            with open(file_path, "w") as f:
                for line in lines: 
                    f.write(f"{line}\n")
        except IOError:
            return False, f"IO error when writing lines to file with file_path '{file_path}'"
        return True, ""

    def append_line(file_path, line):
        try: 
            open(file_path, "a").write(f"{line}\n")
        except FileNotFoundError:
            return False, f"file with file_path '{file_path}' not found"
        except IOError:
            return False, f"IO error when appending line to file with file_path '{file_path}'"
        return True, ""