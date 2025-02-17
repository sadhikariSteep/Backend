# app/routers/user.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.user_schema import UserCreate, UserResponse, LoginRequest, LoginResponse
from app.crud.user_crud import get_user_by_email, create_user, get_users
from app.middleware.rbac import get_current_user, create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database.config import get_db
from datetime import datetime, timedelta, timezone
from app.models.models import User
from fastapi.responses import JSONResponse, RedirectResponse
from onelogin.saml2.auth import OneLogin_Saml2_Auth

from fastapi import APIRouter, Response, Request
from typing import Optional
from starlette.responses import RedirectResponse

from jose import JWTError, jwt
from dotenv import load_dotenv
import os

load_dotenv()


JWT_SECRET = os.getenv("SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(
    prefix="/auth",
    tags=["/auth"],
)


saml_settings_dict = {
  "strict": True, # can set to True to see problems such as Time skew/drift
  "debug": True,
  "idp": {
    "entityId": "urn:deepnet:dual:idp:sso:2fa.steep.de",
    "singleSignOnService": { 
            "url": "https://2fa.steep.de:8074/sso/login",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
    },
    "singleLogoutService": {
            "url": "https://2fa.steep.de:8074/sso/logout",  # IdP Logout URL
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
    "x509cert": "MIIDUDCCAjigAwIBAgIGAX3hD+CiMA0GCSqGSIb3DQEBCwUAMFExCzAJBgNVBAYTAlVLMRkwFwYDVQQKDBBEZWVwbmV0IFNlY3VyaXR5MRAwDgYDVQQLDAdTdXBwb3J0MRUwEwYDVQQDDAxjYS5zdGVlcC5sb2MwIBcNMjExMTIyMDczNDEzWhgPMjEyMDA3MTYwNzM0MTNaMF0xCzAJBgNVBAYTAlVLMRkwFwYDVQQKDBBEZWVwbmV0IFNlY3VyaXR5MRswGQYDVQQLDBJEZWVwbmV0IER1YWxTaGllbGQxFjAUBgNVBAMMDWlkcC5zdGVlcC5sb2MwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC2vUdFRAw1UCioDaeaUWXrr63GjDaQ02kLq564iU2waZJo9HCPeGNCV9QZt138ZK6v5djXlrXaL6qJfXjoHxfCTf9JmvG5XrJiXnBitrASMpvqAF478irsLfsYVADU21og7utaDDFY3YNVjVuomgc/7HtE4b2g3NKVnPtkg54EpJRqtUJp/qLW+ABR3kLSkr/WExiZUfnlXM/mUqKq+dRCd7sKWUIqhPRS0vuDIQ79zah3NDcj4zDlTFx4wNoQ9ESYJgRT/H+Ps5SSOht8JBpgJP4UrVLNkVZOhN+irbzkMKDhHtiBFwzS/2VV1dWOwjAfqMr3n4gF9BcV+VEHqxCXAgMBAAGjIDAeMBwGA1UdEQQVMBOCEUJOMkZBMDEuc3RlZXAubG9jMA0GCSqGSIb3DQEBCwUAA4IBAQAAucbwPoGAlvFixmWkAPz014/rnKgpJe5iKht5I/czDt5+dA0z8ioMkv5Zrl/4WSlAfZ6h/5gTwx6XQOjSEAF6ateFKeD5mETdKjOk+OZyXXlc46iANX61TN+y3jFTSJcuWkpFWZJiZC+0JLHrpYvPMFoqUP+eoTDVqSuLisrtWCY89lu86K/mg4pVNaoNpfVeSVHPp5ZxOj8xkMT6c/n9O8xpOTEPC69SYk0a+8FTCfSjdDCzSDznZPf3pnII632lqEnRBV74H0JJI2u8B4kxPc/zuYCqXIEku2f4/mHDArmk1QNf9jflngOK9bvPQdFShrm/LbrH82X/59dmJMca"
    #"x509cert": "MIIDUDCCAjigAwIBAgIGAX3hD+CiMA0GCSqGSIb3DQEBCwUAMFExCzAJBgNVBAYTAlVLMRkwFwYD VQQKDBBEZWVwbmV0IFNlY3VyaXR5MRAwDgYDVQQLDAdTdXBwb3J0MRUwEwYDVQQDDAxjYS5zdGVl cC5sb2MwIBcNMjExMTIyMDczNDEzWhgPMjEyMDA3MTYwNzM0MTNaMF0xCzAJBgNVBAYTAlVLMRkw FwYDVQQKDBBEZWVwbmV0IFNlY3VyaXR5MRswGQYDVQQLDBJEZWVwbmV0IER1YWxTaGllbGQxFjAU BgNVBAMMDWlkcC5zdGVlcC5sb2MwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC2vUdF RAw1UCioDaeaUWXrr63GjDaQ02kLq564iU2waZJo9HCPeGNCV9QZt138ZK6v5djXlrXaL6qJfXjo HxfCTf9JmvG5XrJiXnBitrASMpvqAF478irsLfsYVADU21og7utaDDFY3YNVjVuomgc/7HtE4b2g 3NKVnPtkg54EpJRqtUJp/qLW+ABR3kLSkr/WExiZUfnlXM/mUqKq+dRCd7sKWUIqhPRS0vuDIQ79 zah3NDcj4zDlTFx4wNoQ9ESYJgRT/H+Ps5SSOht8JBpgJP4UrVLNkVZOhN+irbzkMKDhHtiBFwzS /2VV1dWOwjAfqMr3n4gF9BcV+VEHqxCXAgMBAAGjIDAeMBwGA1UdEQQVMBOCEUJOMkZBMDEuc3Rl ZXAubG9jMA0GCSqGSIb3DQEBCwUAA4IBAQAAucbwPoGAlvFixmWkAPz014/rnKgpJe5iKht5I/cz Dt5+dA0z8ioMkv5Zrl/4WSlAfZ6h/5gTwx6XQOjSEAF6ateFKeD5mETdKjOk+OZyXXlc46iANX61 TN+y3jFTSJcuWkpFWZJiZC+0JLHrpYvPMFoqUP+eoTDVqSuLisrtWCY89lu86K/mg4pVNaoNpfVe SVHPp5ZxOj8xkMT6c/n9O8xpOTEPC69SYk0a+8FTCfSjdDCzSDznZPf3pnII632lqEnRBV74H0JJ I2u8B4kxPc/zuYCqXIEku2f4/mHDArmk1QNf9jflngOK9bvPQdFShrm/LbrH82X/59dmJMca"
  },

  "sp": {
    "entityId": "https://bnkichat.steep.loc/login",
    "assertionConsumerService": {
            "url": "https://bnkichat.steep.loc/auth/api/saml/callback",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
    },
    "singleLogoutService": {
            "url": "https://bnkichat.steep.loc/auth/api/saml/logout",  # Logout URL for SP
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        },
    "x509cert": "MIIEGzCCAwOgAwIBAgIUMr1AA0cB6SkvEDeZxeOGT+jl84gwDQYJKoZIhvcNAQELBQAwgZwxCzAJBgNVBAYTAkRFMQwwCgYDVQQIDANOUlcxDTALBgNVBAcMBEJvbm4xEzARBgNVBAoMCnN0ZWVwIEdtYkgxFjAUBgNVBAsMDUlUIERlcGFydG1lbnQxIzAhBgNVBAMMGmh0dHBzOi8vYm5raWNoYXQuc3RlZXAubG9jMR4wHAYJKoZIhvcNAQkBFg9hZG1pbkBzdGVlcC5sb2MwHhcNMjQxMTI4MjEyNDM1WhcNMzQxMTI4MjEyNDM1WjCBnDELMAkGA1UEBhMCREUxDDAKBgNVBAgMA05SVzENMAsGA1UEBwwEQm9ubjETMBEGA1UECgwKc3RlZXAgR21iSDEWMBQGA1UECwwNSVQgRGVwYXJ0bWVudDEjMCEGA1UEAwwaaHR0cHM6Ly9ibmtpY2hhdC5zdGVlcC5sb2MxHjAcBgkqhkiG9w0BCQEWD2FkbWluQHN0ZWVwLmxvYzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJsrI8+RJK3TgnLS2yai+n0SXMnmKjQ06tQ2dW3tpmIlwUFdM+V4G+nBMySPToCYa10HC8q1NdABRQQnkahjtPt5HhylIXHDgKzAGRE1/O6jvSce4cf1Ax0ADQWzXIETmnwqUwamTPFzV/J9ZRB7di99jpFqkwFTCd2lsIOIIfjXYRVDWyoHPICVppaQ9itlswCZgKeF4pY7+qXOb82k3fkghzDl6LTY4HQdphgFo63kMvnvIm3vJZKkIN4fmsF9L+1eXTWVSHJgZHwK+DQ3k8o0X5Dwtgd5MsjjeXAayBel3PqBYehl+c5qGfeAbdKU41K0f6uno92kR3tnPcYJBcMCAwEAAaNTMFEwHQYDVR0OBBYEFCKotFflahWTVGoFPmGIDiomzbmMMB8GA1UdIwQYMBaAFCKotFflahWTVGoFPmGIDiomzbmMMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAIgXNLEIPAK/h51vEBKZIo+lDk7YGSuZ52ectVIu/fJhE0zz6c6z2bBpSrEgCctZ3l8Wnh9JBbVsficUcKWLOhwMkDdm1JqCfWUlgTnDVeZ9ZyfsXj1aRqrXyLaW+toI872UgX52xY9d3GJF6dSQBTW1zEKJBmLTZycDR4M1veuD/vghxTjiUaiuQuiqEupSKeBVIXBPb8cI7OPCneQkUgKxVcj3sqWh1Eq1RNB10NsPCNPmvfe68RmpiuvUl7t8xK6NFzOmHMgHPSb8WiX17SL8crFVXKFJv68STjYW2zW3L5YQaPaFPU2HEpYFotFGToRy4Vx+A/L284hZGR+KX8g=",
    "privateKey": "MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCbKyPPkSSt04Jy0tsmovp9ElzJ5io0NOrUNnVt7aZiJcFBXTPleBvpwTMkj06AmGtdBwvKtTXQAUUEJ5GoY7T7eR4cpSFxw4CswBkRNfzuo70nHuHH9QMdAA0Fs1yBE5p8KlMGpkzxc1fyfWUQe3YvfY6RapMBUwndpbCDiCH412EVQ1sqBzyAlaaWkPYrZbMAmYCnheKWO/qlzm/NpN35IIcw5ei02OB0HaYYBaOt5DL57yJt7yWSpCDeH5rBfS/tXl01lUhyYGR8Cvg0N5PKNF+Q8LYHeTLI43lwGsgXpdz6gWHoZfnOahn3gG3SlONStH+rp6PdpEd7Zz3GCQXDAgMBAAECggEAMZN/9pKOIIeidyNNZ7PMymcyhENompOJr9HShRPYBCXB8CtiKF/Os0nKGFU9JLMOIoPczaBGGDY/ocsuq5lnuq0A5PARlnJ7SzZ5C9mu/WQNTFF+m895diuM/ZRH6umjgyZWrpo1nTNYFx7fSnvXz+aSxX1CiLrKPSnyEqRNDl7quMe/1ezfe2FLuEreL9jKtMR3nedbbSgnJxnO4cVE2zVrxds+1VgsMy/O643oVRgIgVHQ2d7Mxmt+oP3d8EwP3ip/lknIlEzjT3G6LCHRqve8os2ysvXj6iKCaiECSEIAIIfuSvFOdpULEKyao/V5NZxjG0945dlK/mMGBVM3cQKBgQDNSXafrinxXpEojMTBJyVylJC0LSrsDd95Xu4C3gSG4D1cs0ClSMkmKbViRAp4xaPUTwL3SvGK+15/aNxCvym85bbh8Vs8i75MyaYUTENyPAMpAdXiiXkuy6nMxM9457o8l8uAfPJqZznzq+O8lTFDrheIZhZPLeY3LgpbNTNuiQKBgQDBgCO5l8FmqafIDBbHnzc1usrFh2/82OMJNuwW3sbuFRTp7AWFuoo82PyW3/C0G3YuaEl2g4Tjh0oRcTKuPKsbj/gzVNZbfbdbuv0PQtqeLXSL5uuEhDdEMAHCIVGWpRQgYpypFXuvfEWPxb3VSZCZ2MxxYFwoTV6qjJhuzkqe6wKBgESooFsRpgeLSGNWiWvMivLCi48nWCaxESAHxvUAimUN1JgPf7yIFnaEFp0yAoqYF44niudoklaYceeNC7XrN6ts7Piuf4RFfLUz8C7zvs8TET+C1KU6s2QaS8Unwfg/EIO5hR+JKo65zaEYyUdGYr6vGEHPWwDKaifkZyRQK855AoGARmZ8mPWho9xt8taTIyXGTIIdbCiOkgvG7n9Q/jEnZ0+8QC9jAviPevvnSm1Hgf/Ly66dq8TGAJIkXJw2uDXSe0CyKNrg8oCWyYUKtRa5u3sGQDBP1/LSuLhOq3a73HdLD01ReiMa0QoBtQFYw9T0C0VZfJZ2cSNVIe/tNcNQWukCgYALx7u2xjayTayyERbuLM9WxpzTSahuJCWrxp3JY+5hnwEQP7YJy8/baYu3p4DvXm2MIRT1741gdpzsI6pL1UNjoajjkKgcRwAC+pxYsX0qnnAu1oklMHZffBwQcaUkILdKd70qt2cHKBSk1wajk/ZaBMq/ab4XGeujE7L9v6xc/w=="
  },

   "security": {
        "allowClockSkew": 300  # Allow 5 minutes of clock skew
    },
    
    "clockTolerance": 10  # Allow a 10-second tolerance for clock skew
}

# @router.get("/sp-metadata", response_class=PlainTextResponse)
# async def get_sp_metadata(request: Request):
#     # Create the SAML request object
#     saml_settings = OneLogin_Saml2_Settings()

#     # Get the SAML metadata
#     metadata = saml_settings.get_sp_metadata()

#     # Validate metadata and check for errors
#     errors = saml_settings.validate_metadata(metadata)
#     if len(errors) > 0:
#         return {"error": f"Error found on Metadata: {', '.join(errors)}"}

#     # Return metadata as an XML response
#     return Response(content=metadata, media_type="application/xml")

# @router.get("/login/saml")
# async def saml_login():
#     """
#         Redirect the user to the Idp's single Sign-On (sso) url.
#     """
#     return sso.get_redirect()

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    print("Received user data:", user)  # Log incoming data for debugging
    existing_user = get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db=db, user=user)

@router.get("users/me", response_model=UserResponse)
def read_current_user(current_user: UserResponse=Depends(get_current_user)):
    return current_user

@router.post("/login", response_model=LoginResponse)
async def verifyLogin(user: LoginRequest, db: Session= Depends(get_db)):

    try:
        # retrive user by email
        db_user = get_user_by_email(db, email=user.email)
        print("filter user:", f"user found: {db_user.email}" if db_user else f"no user found with email: {user.email}")

        # Check if user exists
        if db_user is None:
            raise HTTPException(status_code=400, detail="Invalid email ..or password")

        # Verify the password
        # if not verify_password(user.password, db_user.hashed_password):  # Assuming db_user.hashed_password stores the hashed password
        #     print("Password is incorrect.")
        #     raise HTTPException(status_code=400, detail="Invalid email or password")
        if verify_password(user.password, db_user.hashed_password):
            print("Password is correct!")

        else:
            print("Password is incorrect.")  
            raise HTTPException(status_code=400, detail="Invalid email or password")
        # Create and return access token
        # access_token_expires = timedelta(minutes=30)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": db_user.email}, expires_delta=access_token_expires)
    
        #return {"access_token": access_token, "token_type": "bearer"}
        # Construct the response including all required fields
        response_data = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            id=db_user.id,
            name=db_user.name,
            email=db_user.email,
            created_at=db_user.created_at
        )
        response = (response_data)
        print("Response data:: ", response)
        return response
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal ddServer Error")


@router.get("/users/")
def read_users(db: Session = Depends(get_db)):
    users = get_users(db)
    print("users: ", users)
    return users

async def prepare_from_fastapi_request(request, debug=False):


    # Check if the scheme is https (use the x-forwarded-proto header if behind a proxy)
    url_scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    print("which header: ", url_scheme)
    http_host = request.headers.get("x-forwarded-host")#, request.url.hostname)
    print("host: ", http_host)# , request.client.host)
    #  If there are multiple values for x-forwarded-host, pick the first one
    if http_host:
        http_host = http_host.split(',')[0].strip()  # Split by commas and take the first value
    if not http_host:
        http_host = request.url.hostname

    print("hosts: ", http_host)# 
    # get data from form
    form_data = await request.form()
    #print("form_DAta", form_data)
    rv = {
        "http_host": http_host,
        "server_port": request.url.port or (443 if url_scheme == "https" else 80),
        "script_name": request.url.path,
        "post_data": { },
        "get_data": { }
        # Advanced request options
        # "https": "",
        # "request_uri": "",
        # "query_string": "",
        # "validate_signature_from_qs": False,
        # "lowercase_urlencoding": False
    }
    if (request.query_params):
         rv["get_data"] = dict(request.query_params)

    if "SAMLResponse" in form_data:
        
        SAMLResponse = form_data["SAMLResponse"]
        #print("formsmla:", SAMLResponse)
        rv["post_data"]["SAMLResponse"] = SAMLResponse
    if "RelayState" in form_data:
        RelayState = form_data["RelayState"]
        rv["post_data"]["RelayState"] = RelayState
    #print(f"Request Data: {rv}")  # Debugging print, can be removed in production
    return rv

@router.get('/api/saml/login')
async def saml_login(request: Request):
    """
    Handle the SAML login request.
    """
    req = await prepare_from_fastapi_request(request)
    # Initialize SAML Authentication
    auth = OneLogin_Saml2_Auth(req, saml_settings_dict)
    
    # Redirect user to IdP for login
    callback_url = auth.login()
    #print("callback url : ", callback_url)
    return RedirectResponse(url=callback_url)

@router.get("/")
async def root():
  return { "message": "Hello World" }

@router.post('/api/saml/callback')
async def saml_login_callback(request: Request, db: Session = Depends(get_db)):
  
    req = await prepare_from_fastapi_request(request)
    auth = OneLogin_Saml2_Auth(req, saml_settings_dict)

    auth.process_response() # Process IdP response
    errors = auth.get_errors() # This method receives an array with the errors

    # If there are errors, log them
    if errors:
        return JSONResponse(status_code=401, content={"message": "Authentication failed", "errors": errors})
    
    
    # If authenticated, log the user's data (debugging)
    user_data = auth.get_attributes()
    # Add session timeout data (for illustration)
    session_data = {
        "email": user_data.get("EMAIL", [None])[0],
        "pretty_name": user_data.get("PRETTYNAME", [None])[0],
        "groups": user_data.get("groups", []),
        "profile_id": user_data.get("profileId", [None])[0],
        "session_timeout_abs": user_data.get("sessionTimeoutAbs", [None])[0],
        "session_idle_time": user_data.get("sessionIdleTime", [None])[0],
        "session_timeout": user_data.get("sessionTimeout", [None])[0],
    }
    print("logged in email: ", session_data['email'], session_data['profile_id'])
    print("its me")

    # Save or update user data in the database
    existing_user = db.query(User).filter(User.email == session_data['email']).first()

    if not existing_user:

        # If user does not exist, create a new user record
        new_user = User(
            steep_id=session_data['profile_id'],
            email=session_data['email'],
            name=session_data['pretty_name'],
        )
        db.add(new_user)
        db.commit()  # Commit the new user record to the database
        db.refresh(new_user)  # Get the newly added user data

    # Generate JWT Token
    token = jwt.encode(
        {**session_data, "exp": datetime.now(timezone.utc) + timedelta(seconds=int(session_data["session_timeout"]))},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    response = RedirectResponse(url="https://bnkichat.steep.loc/chat/", status_code=302)
    response.set_cookie(
        key="auth_token", 
        value=token, 
        httponly=False, 
        secure=True,  # Ensure the cookie is sent only over HTTPS
        samesite="None",  # Prevents CSRF
        domain=".steep.loc",
        max_age=3600  # Token expiration time
    )
    return response

def get_user_id_from_token(request: Request, db: Session = Depends(get_db)):
    """
    Retrieves the user ID from the JWT token stored in cookies.
    
    Args:
        request: FastAPI request object.
        db: SQLAlchemy session for querying the database.

    Returns:
        int: The user ID.

    Raises:
        HTTPException: If the token is missing, expired, invalid, or the user is not found.
    """
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Decode the token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token: Email not found")

        # Query the database to find the user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user.id

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")


  
@router.get("/api/saml/logout")
async def saml_logout(request: Request):
    """
    Handle SAML Single Logout (SLO).
    """
    try:
        # Initialize SAML Authentication
        saml_auth = OneLogin_Saml2_Auth(_prepare_saml_request(request))

        # Get SLO URL and initiate the logout process
        slo_url = saml_auth.logout()

        # Check if a redirect URL is provided by the IdP
        if slo_url:
            return Response(status_code=302, headers={"Location": slo_url})

        # If no redirect URL, logout locally
        return {"message": "Logged out locally. No SLO URL from IdP."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during SAML logout: {str(e)}")


@router.post("/api/saml/logout/callback")
async def saml_logout_callback(request: Request):
    """
    Handle SAML Single Logout Response from the IdP.
    """
    try:
        # Initialize SAML Authentication
        saml_auth = OneLogin_Saml2_Auth(_prepare_saml_request(request))
        saml_auth.process_slo()

        # Check for errors during SLO processing
        errors = saml_auth.get_errors()
        if errors:
            raise HTTPException(status_code=400, detail=f"SAML SLO errors: {errors}")

        # Clear user session (custom logic, e.g., clearing tokens/cookies)
        # Example: request.session.clear() or similar for your session handler

        return {"message": "Logout successful."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during SAML logout callback: {str(e)}")


def _prepare_saml_request(request: Request) -> dict:
    """
    Prepare a SAML request for OneLogin's library.
    """
    url_scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    return {
        "http_host": request.headers["host"],
        "server_port": request.url.port or ("443" if url_scheme == "https" else "80"),
        "script_name": request.url.path,
        "get_data": request.query_params,
        "post_data": request.form() if request.method == "POST" else {},
    }



@router.post("/test/create-user", status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create a new user
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        steep_id=user_data.steep_id,
    )
    db.add(new_user)
    db.commit()  # Save to the database
    db.refresh(new_user)  # Refresh to get the new user's data

    return {"message": "User created successfully", "user": {
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
        "steep_id": new_user.steep_id,
    }}