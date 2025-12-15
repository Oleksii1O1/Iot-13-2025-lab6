import os
import logging
from functools import wraps
import xml.etree.ElementTree as ET


class CustomFileNotFoundError(Exception):
    """Exception raised when the file is not found."""
    pass


class FileCorruptedError(Exception):
    """Exception raised when the file is corrupted or unreadable."""
    pass


def logged(exception_type, mode="console"):
    """
    Decorator for logging function calls and exceptions.
    
    Args:
        exception_type: The specific exception class to catch and log.
        mode (str): Logging mode, either 'console' or 'file'.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__name__)
            logger.setLevel(logging.INFO)
            # Clear existing handlers to avoid duplicate logs
            logger.handlers.clear()
            
            # Select the appropriate handler based on the mode
            if mode == "console":
                handler = logging.StreamHandler()
            else:
                handler = logging.FileHandler(
                    "file_operations.log", encoding='utf-8'
                )
            
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
            
            try:
                logger.info(f"Calling {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"{func.__name__} executed successfully")
                return result
            except exception_type as e:
                logger.error(f"{exception_type.__name__}: {e}")
                raise
            finally:
                # Clean up handlers to prevent memory leaks or open files
                handler.close()
                logger.removeHandler(handler)
        return wrapper
    return decorator


class XMLFileHandler:
    """Class to handle XML file operations (read, write, append)."""

    def __init__(self, filepath):
        self.filepath = filepath
        if not os.path.exists(filepath):
            raise CustomFileNotFoundError(f"File not found: {filepath}")
    
    @logged(FileCorruptedError, mode="console")
    def read(self):
        """Reads the XML file and returns the root element."""
        try:
            return ET.parse(self.filepath).getroot()
        except ET.ParseError as e:
            raise FileCorruptedError(self.filepath, f"XML error: {e}")
        except PermissionError:
            raise FileCorruptedError(self.filepath, "Permission denied")
        except Exception as e:
            raise FileCorruptedError(self.filepath, str(e))
    
    @logged(FileCorruptedError, mode="file")
    def write(self, root):
        """Overwrites the XML file with the provided root element."""
        try:
            tree = ET.ElementTree(root)
            # Indent for pretty printing (requires Python 3.9+)
            ET.indent(tree, space="  ")
            tree.write(
                self.filepath, encoding='utf-8', xml_declaration=True
            )
        except PermissionError:
            raise FileCorruptedError(self.filepath, "Permission denied")
        except Exception as e:
            raise FileCorruptedError(self.filepath, str(e))
    
    @logged(FileCorruptedError, mode="file")
    def append(self, new_element):
        """Appends a new element to the root of the existing XML file."""
        try:
            tree = ET.parse(self.filepath)
            tree.getroot().append(new_element)
            ET.indent(tree, space="  ")
            tree.write(
                self.filepath, encoding='utf-8', xml_declaration=True
            )
        except ET.ParseError as e:
            raise FileCorruptedError(self.filepath, f"XML error: {e}")
        except PermissionError:
            raise FileCorruptedError(self.filepath, "Permission denied")
        except Exception as e:
            raise FileCorruptedError(self.filepath, str(e))


if __name__ == "__main__":
    # Logic to switch between a simple error test and a full demo
    # based on the existence of the log file.
    
    if not os.path.exists("file_operations.log"):
        print("--- Attempting to open non-existent 'demo.xml' ---")
        try:
            handler = XMLFileHandler("demo.xml")
        except CustomFileNotFoundError as e:
            print(f"Caught expected error: {e}")
        
        print("\n--- Creating log file via decorator ---")
        # Create a temporary file to trigger the logging mechanism
        temp_root = ET.Element("temp")
        ET.ElementTree(temp_root).write(
            "temp.xml", encoding='utf-8', xml_declaration=True
        )
        
        # This write operation will generate the log file
        XMLFileHandler("temp.xml").write(temp_root)
        os.remove("temp.xml")
        print("Log file created. Run the script again to see the full demo.")
    
    else:
        # Full demonstration of functionality
        root = ET.Element("data")
        ET.SubElement(root, "item", id="1").text = "First Element"
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write("demo.xml", encoding='utf-8', xml_declaration=True)
        print("--- File 'demo.xml' created ---")
        
        handler = XMLFileHandler("demo.xml")
        
        print("\n--- Reading file: ---")
        # Note: XMLFileHandler.read() returns an Element, 
        # so we iterate over its children.
        root_element = handler.read()
        for child in root_element:
            print(f"   - <{child.tag} id='{child.get('id')}'>"
                  f"{child.text}</{child.tag}>")
        
        print("\n--- Appending element: ---")
        # Create a new element from string and append it
        new_item = ET.fromstring('<item id="2">Second Element</item>')
        handler.append(new_item)
        print("Element appended.")
        
        print("\n--- Reading updated file: ---")
        root_element = handler.read()
        for child in root_element:
            print(f"   - <{child.tag} id='{child.get('id')}'>"
                  f"{child.text}</{child.tag}>")
        
        print("\n--- Overwriting file: ---")
        new_root = ET.Element("data")
        ET.SubElement(new_root, "item", id="100").text = "New Content"
        handler.write(new_root)
        print("File overwritten.")
        
        print("\n--- Reading overwritten file: ---")
        root_element = handler.read()
        for child in root_element:
            print(f"   - <{child.tag} id='{child.get('id')}'>"
                  f"{child.text}</{child.tag}>")
