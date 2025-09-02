#!/usr/bin/env python3
"""
JWT Token Generator for Titanic ML Service

This script generates JWT tokens for testing the authentication system.
It uses the same configuration and signing keys as the ML service.

Usage:
    python scripts/generate_jwt.py --user-id test123 --expires-in 3600
    python scripts/generate_jwt.py --user-id admin --username admin_user --expires-in 7200
"""

import argparse
import sys
import os
from datetime import timedelta, datetime, timezone

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.config import config_manager
from app.auth import auth_service


def generate_token(user_id: str, username: str = None, expires_in: int = 3600) -> str:
    """
    Generate a JWT token for testing.

    Args:
        user_id (str): User identifier
        username (str, optional): Username for the token
        expires_in (int): Token expiration time in seconds

    Returns:
        str: Generated JWT token
    """
    # Prepare token data
    token_data = {"user_id": user_id}
    if username:
        token_data["username"] = username

    # Set custom expiration
    expires_delta = timedelta(seconds=expires_in)

    # Generate token
    token = auth_service.create_access_token(
        data=token_data, expires_delta=expires_delta
    )

    return token


def main():
    """Main function to generate JWT tokens via command line."""
    parser = argparse.ArgumentParser(
        description="Generate JWT tokens for ML Service testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate token for user 'test123' valid for 1 hour:
    python scripts/generate_jwt.py --user-id test123

  Generate token with custom username and 2-hour expiration:
    python scripts/generate_jwt.py --user-id admin --username admin_user --expires-in 7200

  Generate token for testing predictions:
    python scripts/generate_jwt.py --user-id tester --expires-in 600
        """,
    )

    parser.add_argument(
        "--user-id", required=True, help="User ID to include in the token"
    )

    parser.add_argument("--username", help="Optional username to include in the token")

    parser.add_argument(
        "--expires-in",
        type=int,
        default=3600,
        help="Token expiration time in seconds (default: 3600 = 1 hour)",
    )

    args = parser.parse_args()

    try:
        print("🔑 JWT Token Generator for ML Service")
        print("=" * 50)

        # Load configuration
        print("Loading configuration...")
        config_manager.load_config()

        # Generate token
        print(f"Generating token for user: {args.user_id}")
        if args.username:
            print(f"Username: {args.username}")
        print(
            f"Expires in: {args.expires_in} seconds ({args.expires_in // 60} minutes)"
        )

        token = generate_token(
            user_id=args.user_id, username=args.username, expires_in=args.expires_in
        )

        # Calculate expiration time
        exp_time = datetime.now(timezone.utc) + timedelta(seconds=args.expires_in)

        print("\n✅ Token generated successfully!")
        print("=" * 50)
        print("JWT TOKEN:")
        print(token)
        print("=" * 50)
        print(f"Valid until: {exp_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        print("\n📋 Usage Example:")
        print("curl -X POST http://localhost:8000/predict \\")
        print('  -H "Authorization: Bearer ' + token[:20] + '..." \\')
        print('  -H "Content-Type: application/json" \\')
        print(
            '  -d \'{"pclass": 1, "sex": "female", "age": 25, "sibsp": 0, "parch": 0, "fare": 100, "embarked": "S"}\''
        )

    except Exception as e:
        print(f"❌ Error generating token: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
