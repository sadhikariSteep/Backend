# # app/utils.py
# from jose import JWTError, jwt
# from fastapi import Depends, HTTPException
# from app.model.user_model import User
# from app.crud.user_crud import get_user_by_email # Import your user CRUD functions
# from app.database.config import get_db
# from sqlalchemy.orm import Session

# SECRET_KEY = "your_secret_key"  # Replace with your actual secret key
# ALGORITHM = "HS256"              # Algorithm used for signing the JWT

# def verify_token(token: str, db: Session = Depends(get_db)) -> User:
#     credentials_exception = HTTPException(
#         status_code=401,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#         user = get_user_by_email(db, email=email)
#         if user is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     return user
