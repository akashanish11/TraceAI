# Authentication Service Identity Failure

## System Overview

AuthService uses IdentityService to authenticate users
and obtain authentication tokens.

## Authentication Behavior

The authentication request contains user credentials.
IdentityService validates the credentials before issuing
an authentication token.

## Failure Behavior

If the credentials are invalid:

1. IdentityService rejects the authentication request.
2. AuthService cannot obtain an authentication token.
3. The user authentication request fails.
4. Access is denied.

## Expected Diagnostic Signal

An authentication failure typically produces:

- Authentication failed
- Invalid credentials
- AuthenticationError
- Unable to authenticate
- Access denied

## Relevant Components

- AuthService
- IdentityService
- identity_client.request_token()