from collections import UserDict
from datetime import datetime, timedelta


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if value is None or value == "":
            raise ValueError("Ім'я повинно бути заповненим")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value: str):
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Телефон повинен містити 10 цифр")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y")
            if birthday.strftime("%d.%m.%Y") != value:
                raise ValueError
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

        super().__init__(birthday)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        found_phone = self.find_phone(phone)
        if found_phone is None:
            raise ValueError("Телефон не знайдено")
        self.phones.remove(found_phone)

    def edit_phone(self, old_phone, new_phone):
        found_phone = self.find_phone(old_phone)
        if found_phone is None:
            raise ValueError("Телефон не знайдено")
        self.phones[self.phones.index(found_phone)] = Phone(new_phone)

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday = str(self.birthday) if self.birthday is not None else "не вказано"
        return (
            f"Ім'я: {self.name}, телефони: {phones}, "
            f"день народження: {birthday}"
        )


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = record.birthday.value.date()

            # Для 29 лютого в невисокосному році використовуємо 28 лютого.
            try:
                birthday_this_year = birthday.replace(year=today.year)
            except ValueError:
                birthday_this_year = birthday.replace(year=today.year, day=28)

            if birthday_this_year < today:
                try:
                    birthday_this_year = birthday.replace(year=today.year + 1)
                except ValueError:
                    birthday_this_year = birthday.replace(
                        year=today.year + 1, day=28
                    )

            days_until_birthday = (birthday_this_year - today).days

            if 0 <= days_until_birthday < 7:
                congratulation_date = birthday_this_year

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

        return upcoming_birthdays


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            return f"Помилка: {error}"
        except KeyError:
            return "Контакт не знайдено"
        except IndexError:
            return "Недостатньо аргументів для команди"

    return inner


def parse_input(user_input):
    parts = user_input.split()
    if not parts:
        return "", []

    command, *args = parts
    return command.lower(), args


@input_error
def add_contact(args, book):
    if len(args) != 2:
        return "Використання: add [ім'я] [телефон]"

    name, phone = args
    record = book.find(name)

    if record is None:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return "Контакт додано"

    record.add_phone(phone)
    return "Телефон додано до контакту"


@input_error
def change_contact(args, book):
    if len(args) != 3:
        return "Використання: change [ім'я] [старий телефон] [новий телефон]"

    name, old_phone, new_phone = args
    record = book.find(name)

    if record is None:
        raise KeyError(name)

    record.edit_phone(old_phone, new_phone)
    return "Телефон змінено"


@input_error
def show_phone(args, book):
    if len(args) != 1:
        return "Використання: phone [ім'я]"

    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError(name)

    if not record.phones:
        return "Телефони не вказані"

    return "; ".join(p.value for p in record.phones)


@input_error
def show_all(args, book):
    if args:
        return "Команда all не потребує аргументів"

    if not book:
        return "Адресна книга порожня"

    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book):
    if len(args) != 2:
        return "Використання: add-birthday [ім'я] [DD.MM.YYYY]"

    name, birthday = args
    record = book.find(name)

    if record is None:
        raise KeyError(name)

    record.add_birthday(birthday)
    return "День народження збережено"


@input_error
def show_birthday(args, book):
    if len(args) != 1:
        return "Використання: show-birthday [ім'я]"

    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError(name)

    if record.birthday is None:
        return "День народження не вказано"

    return str(record.birthday)


@input_error
def birthdays(args, book):
    if args:
        return "Команда birthdays не потребує аргументів"

    upcoming = book.get_upcoming_birthdays()

    if not upcoming:
        return "Протягом наступних 7 днів днів народження немає"

    return "\n".join(
        f"{contact['name']}: {contact['congratulation_date']}"
        for contact in upcoming
    )


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
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(args, book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()