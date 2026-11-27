from collections import UserDict
from datetime import datetime, timedelta
import re


# Класи для зберігання контактів

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Name cannot be empty.")

        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if (
            not isinstance(value, str)
            or len(value) != 10
            or not value.isascii()
            or not value.isdigit()
        ):
            raise ValueError("Phone must contain exactly 10 digits.")

        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            if not isinstance(value, str) or not re.fullmatch(
                r"[0-9]{2}\.[0-9]{2}\.[0-9]{4}", value
            ):
                raise ValueError

            birthday = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY") from None

        super().__init__(birthday)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        found_phone = self.find_phone(phone)

        if found_phone is None:
            raise ValueError("Phone not found.")

        self.phones.remove(found_phone)

    def edit_phone(self, old_phone, new_phone):
        found_phone = self.find_phone(old_phone)

        if found_phone is None:
            raise ValueError("Phone not found.")

        # Перевіряємо новий номер перед зміною старого.
        validated_phone = Phone(new_phone)
        found_phone.value = validated_phone.value

    def find_phone(self, phone):
        for saved_phone in self.phones:
            if saved_phone.value == phone:
                return saved_phone

        return None

    def __str__(self):
        phones = "; ".join(phone.value for phone in self.phones)
        birthday = str(self.birthday) if self.birthday else "not set"
        return (
            f"Contact name: {self.name.value}, phones: {phones}, "
                        f"birthday: {birthday}"
        )


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        self.data.pop(name, None)

    def get_upcoming_birthdays(self):
        # Перевіряємо сьогодні та наступні шість днів.
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = record.birthday.value.date()
            year = today.year

            while True:
                try:
                    next_birthday = birthday.replace(year=year)
                except ValueError:
                    # Для 29 лютого у невисокосний рік обираємо 28 лютого.
                    next_birthday = birthday.replace(year=year, day=28)

                if next_birthday >= today:
                    break
                year += 1

            if (next_birthday - today).days < 7:
                congratulation_date = next_birthday

                if congratulation_date.weekday() >= 5:
                    congratulation_date += timedelta(
                        days=7 - congratulation_date.weekday()
                    )

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime(
                        "%d.%m.%Y"
                    ),
                })

        upcoming_birthdays.sort(
            key=lambda contact: datetime.strptime(
                contact["congratulation_date"], "%d.%m.%Y"
            )
        )
        return upcoming_birthdays


# Обробка помилок

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            return str(error)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter user name."

    return inner


# Розбір команди

def parse_input(user_input):
    parts = user_input.strip().split()
    cmd = parts[0].lower() if parts else ""
    args = parts[1:]
    return cmd, args


# Обробники команд

@input_error
def hello_handler():
    return "How can I help you?"


@input_error
def add_contact(args, book):
    if len(args) != 2:
        raise ValueError("Usage: add <username> <phone>")

    username, phone = args
    record = book.find(username)

    if record is None:
        record = Record(username)
        record.add_phone(phone)
        book.add_record(record)
        return "Contact added."

    record.add_phone(phone)
    return "Phone added."


@input_error
def change_contact(args, book):
    if len(args) != 3:
        raise ValueError(
            "Usage: change <username> <old_phone> <new_phone>"
        )

    username, old_phone, new_phone = args
    record = book.find(username)

    if record is None:
        raise KeyError(username)

    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def get_phone(args, book):
    username = args[0]

    if len(args) != 1:
        raise ValueError("Usage: phone <username>")

    record = book.find(username)

    if record is None:
        raise KeyError(username)

    if not record.phones:
        return "No phones found."

    return "; ".join(phone.value for phone in record.phones)


@input_error
def get_all_contacts(book):
    if not book:
        return "No contacts found."

    return "\n".join(str(record) for record in book.values())


@input_error
def remove_phone_handler(args, book):
    if len(args) != 2:
        raise ValueError("Usage: remove-phone <username> <phone>")

    username, phone = args
    record = book.find(username)

    if record is None:
        raise KeyError(username)

    record.remove_phone(phone)
    return "Phone removed."


@input_error
def delete_contact(args, book):
    if len(args) != 1:
        raise ValueError("Usage: delete <username>")

    username = args[0]

    if book.find(username) is None:
        raise KeyError(username)

    book.delete(username)
    return "Contact deleted."


@input_error
def add_birthday(args, book):
    if len(args) != 2:
        raise ValueError("Usage: add-birthday <username> <DD.MM.YYYY>")

    username, birthday = args
    record = book.find(username)

    if record is None:
        raise KeyError(username)

    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book):
    if len(args) != 1:
        raise ValueError("Usage: show-birthday <username>")

    username = args[0]
    record = book.find(username)

    if record is None:
        raise KeyError(username)

    if record.birthday is None:
        return "Birthday not set."

    return str(record.birthday)


@input_error
def birthdays(args, book):
    if args:
        raise ValueError("Usage: birthdays")

    upcoming_birthdays = book.get_upcoming_birthdays()

    if not upcoming_birthdays:
        return "No upcoming birthdays."

    return "\n".join(
        f"{contact['name']}: {contact['congratulation_date']}"
        for contact in upcoming_birthdays
    )


# Головний цикл бота

def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print(hello_handler())

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(get_phone(args, book))

        elif command == "all":
            print(get_all_contacts(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        elif command == "remove-phone":
            print(remove_phone_handler(args, book))

        elif command == "delete":
            print(delete_contact(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
