import os
import logging
from functools import wraps
import xml.etree.ElementTree as ET


class FileNotFoundError(Exception):
    """Виняток, коли файл не знайдено"""
    pass


class FileCorruptedError(Exception):
    """Виняток, коли файл пошкоджено"""
    pass


class InvalidFileTypeError(Exception):
    """Виняток, коли файл не .xml"""
    pass


def logged(exception_type=Exception, mode="console"):
    """Декоратор для логування операцій"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__name__)
            logger.setLevel(logging.INFO)
            logger.handlers.clear()

            handler = (logging.StreamHandler() if mode == "console"
                      else logging.FileHandler("file_operations.log",
                                               encoding="utf-8"))
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            logger.addHandler(handler)

            try:
                filepath = args[0].filepath if args else "невідомо"
                logger.info(f"Файл: {filepath} | {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"Файл: {filepath} | {func.__name__} успішно")
                return result
            except exception_type as e:
                filepath = args[0].filepath if args else "невідомо"
                logger.error(f"Файл: {filepath} | {type(e).__name__}: {e}")
                raise
            finally:
                handler.close()
                logger.removeHandler(handler)

        return wrapper
    return decorator


class XMLFileHandler:
    """Клас для роботи з XML файлами"""

    def __init__(self, filepath):
        """Ініціалізація обробника XML файлів"""
        self.filepath = os.path.abspath(filepath)

        if os.path.splitext(self.filepath)[1].lower() != '.xml':
            raise InvalidFileTypeError(
                f"Файл повинен мати розширення .xml"
            )
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Файл '{self.filepath}' не знайдено")
        if not os.path.isfile(self.filepath):
            raise FileCorruptedError(f"'{self.filepath}' не є файлом")

    @logged(exception_type=Exception, mode="console")
    def read(self):
        """Читання XML файлу"""
        try:
            tree = ET.parse(self.filepath)
            return ET.tostring(tree.getroot(), encoding='unicode')
        except ET.ParseError as e:
            raise FileCorruptedError(f"Помилка парсингу: {e}")
        except PermissionError:
            raise FileCorruptedError("Немає прав доступу")

    @logged(exception_type=Exception, mode="file")
    def write(self, content):
        """Запис у XML файл"""
        try:
            root = ET.fromstring(content)
            ET.ElementTree(root).write(
                self.filepath, encoding='utf-8', xml_declaration=True
            )
        except ET.ParseError as e:
            raise FileCorruptedError(f"Невалідний XML: {e}")
        except PermissionError:
            raise FileCorruptedError("Немає прав доступу")

    @logged(exception_type=Exception, mode="file")
    def append(self, element_data):
        """Дописування елементу в XML"""
        try:
            tree = ET.parse(self.filepath)
            root = tree.getroot()
            elem = ET.SubElement(
                root,
                element_data.get('tag', 'item'),
                attrib=element_data.get('attrib', {})
            )
            elem.text = element_data.get('text', '')
            tree.write(
                self.filepath, encoding='utf-8', xml_declaration=True
            )
        except ET.ParseError as e:
            raise FileCorruptedError(f"Файл пошкоджено: {e}")
        except PermissionError:
            raise FileCorruptedError("Немає прав доступу")


if __name__ == "__main__":
    print("=== Тест 1: Файл без .xml ===")
    try:
        XMLFileHandler("test.txt")
    except InvalidFileTypeError as e:
        print(f"✓ {e}")

    print("\n=== Тест 2: Неіснуючий XML ===")
    try:
        XMLFileHandler("missing.xml")
    except FileNotFoundError as e:
        print(f"✓ {e}")

    print("\n=== Тест 3: Робота з XML ===")
    test_file = "demo.xml"
    if os.path.exists(test_file):
        try:
            h = XMLFileHandler(test_file)
            print("Читання:", h.read()[:80] + "...")
            h.append({'tag': 'item', 'text': 'Тест', 'attrib': {'id': '1'}})
            print("✓ Елемент додано")
        except Exception as e:
            print(f"Помилка: {e}")
    else:
        print(f"Створіть '{test_file}' для тесту")

    print("\n✓ Логи: 'file_operations.log'")