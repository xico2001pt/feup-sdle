from .file_io import FileIO
import pathlib

class ClientIO:

    def save_client_id(client_dir, client_id):
        if not pathlib.Path(client_dir).exists():
            pathlib.Path(client_dir).mkdir(parents=True)
        
        try: 
            open(f"{client_dir}/id.txt", 'w').write(client_id)
        except IOError:
            raise IOError("Could not save the client_id to file")
        return True

    def read_client_id(client_dir):
        path = f"{client_dir}/id.txt"
        if not pathlib.Path(path).exists():
            return None
        
        try: 
            return open(path, "r").read()
        except IOError:
            raise IOError("Failed to read client id")

    def save_client_counter(client_dir, counter):
        if not pathlib.Path(client_dir).exists():
            pathlib.Path(client_dir).mkdir(parents=True)
        
        try: 
            open(f"{client_dir}/counter.txt", "w").write(str(counter))
        except IOError:
            return IOError("Could not save client counter")
        return True

    def read_client_counter(client_dir):
        path = f"{client_dir}/counter.txt"
        if not pathlib.Path(path).exists():
            return 0
        
        try: 
            return int(open(path, "r").read())
        except ValueError:
            raise ValueError("Could not parse client counter to integer type")
        except IOError:
            raise IOError("Could not read client counter")

    def save_client_topics(client_dir, last_publications_read):
        if not pathlib.Path(client_dir).exists():
            pathlib.Path(client_dir).mkdir(parents=True)

        result, error_str = FileIO.write_lines(f"{client_dir}/topics.csv", [f"{topic_id},{last_publication}" for topic_id, last_publication in last_publications_read.items()])
        if not result:
            raise IOError(error_str)

    def read_client_topics(client_dir):
        path = f"{client_dir}/topics.csv"
        if not pathlib.Path(path).exists():
            return {}

        result, lines = FileIO.read_lines(path)
        if not result:
            raise IOError(lines)
        else:
            last_publications_read = {}
            for line in lines:
                topic_id, last_publication = line.strip().split(",")
                try:
                    last_publications_read[topic_id] = int(last_publication)
                except ValueError as e:
                    raise ValueError("Could not parse last publication read from a topic to integer type")
            return last_publications_read