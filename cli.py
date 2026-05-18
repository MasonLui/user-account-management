"""
Command-line admin interface for User Account Manager.

Usage:
    python cli.py list [--archived]
    python cli.py create <username> <email> <password> [--admin]
    python cli.py update-password <username> <new_password>
    python cli.py archive <username>
    python cli.py unarchive <username>
"""
import argparse
import datetime
import sys

from auth import hash_password
from logger import logger
from models import NotFoundError, users


def _print_user(user):
    status = '[ARCHIVED]' if user.archived else '[ACTIVE] '
    admin = '[ADMIN]' if user.is_admin else '       '
    print(f'{status} {admin}  {user.username:<20} {user.email:<30}  created {user.created_at}')


def cmd_list(archived_only: bool):
    all_users = list(users())
    filtered = [u for u in all_users if u.archived == archived_only]
    if not filtered:
        print('No users found.')
        return
    header = 'Archived users:' if archived_only else 'Active users:'
    print(f'\n{header}\n' + '-' * 72)
    for u in filtered:
        _print_user(u)
    print()


def cmd_create(username: str, email: str, password: str, is_admin: bool):
    try:
        users[username]
        print(f"Error: username '{username}' already exists.")
        sys.exit(1)
    except NotFoundError:
        pass

    users.insert(dict(
        username=username,
        email=email,
        pwd=hash_password(password),
        is_admin=is_admin,
        archived=False,
        created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
    ))
    logger.info(f'CLI: created user {username} (admin={is_admin})')
    print(f"User '{username}' created successfully.")


def cmd_update_password(username: str, new_password: str):
    try:
        users[username]
    except NotFoundError:
        print(f"Error: user '{username}' not found.")
        sys.exit(1)

    users.update({'pwd': hash_password(new_password)}, username)
    logger.info(f'CLI: updated password for {username}')
    print(f"Password updated for '{username}'.")


def cmd_archive(username: str):
    try:
        users[username]
    except NotFoundError:
        print(f"Error: user '{username}' not found.")
        sys.exit(1)

    users.update({'archived': True}, username)
    logger.info(f'CLI: archived user {username}')
    print(f"User '{username}' archived.")


def cmd_unarchive(username: str):
    try:
        users[username]
    except NotFoundError:
        print(f"Error: user '{username}' not found.")
        sys.exit(1)

    users.update({'archived': False}, username)
    logger.info(f'CLI: unarchived user {username}')
    print(f"User '{username}' unarchived.")


def main():
    parser = argparse.ArgumentParser(
        description='User Account Manager – CLI admin tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest='command', metavar='command')
    sub.required = True

    # list
    p_list = sub.add_parser('list', help='List users')
    p_list.add_argument('--archived', action='store_true', help='Show archived users only')

    # create
    p_create = sub.add_parser('create', help='Create a new user')
    p_create.add_argument('username')
    p_create.add_argument('email')
    p_create.add_argument('password')
    p_create.add_argument('--admin', action='store_true', help='Grant admin privileges')

    # update-password
    p_pwd = sub.add_parser('update-password', help='Update a user\'s password')
    p_pwd.add_argument('username')
    p_pwd.add_argument('new_password')

    # archive
    p_arch = sub.add_parser('archive', help='Archive a user account')
    p_arch.add_argument('username')

    # unarchive
    p_unarch = sub.add_parser('unarchive', help='Unarchive a user account')
    p_unarch.add_argument('username')

    args = parser.parse_args()

    if args.command == 'list':
        cmd_list(archived_only=args.archived)
    elif args.command == 'create':
        cmd_create(args.username, args.email, args.password, is_admin=args.admin)
    elif args.command == 'update-password':
        cmd_update_password(args.username, args.new_password)
    elif args.command == 'archive':
        cmd_archive(args.username)
    elif args.command == 'unarchive':
        cmd_unarchive(args.username)


if __name__ == '__main__':
    main()
