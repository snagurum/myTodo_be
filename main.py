from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import uvicorn

from database import get_db, create_tables, User, Todo
from schemas import UserCreate, UserLogin, User as UserSchema, TodoCreate, TodoUpdate, Todo as TodoSchema, Token
from auth import authenticate_user, create_access_token, get_current_user, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from redis_client import cache

app = FastAPI(title="MyTodo API", description="Todo List API with authentication and caching")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    create_tables()

@app.post("/register", response_model=UserSchema)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        mobile_no=user.mobile_no,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/todos", response_model=List[TodoSchema])
def get_todos(
    completed: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Try to get from cache first
    cache_key = f"todos_user_{current_user.id}_completed_{completed}"
    cached_todos = cache.get(cache_key)
    if cached_todos:
        return cached_todos
    
    # Query from database
    query = db.query(Todo).filter(Todo.owner_id == current_user.id)
    if completed is not None:
        query = query.filter(Todo.completed == completed)
    
    todos = query.order_by(Todo.created_at.desc()).all()
    
    # Convert to dict for caching
    todos_dict = [TodoSchema.from_orm(todo).dict() for todo in todos]
    cache.set(cache_key, todos_dict, expire=60)  # Cache for 1 minute
    
    return todos

@app.post("/todos", response_model=TodoSchema)
def create_todo(
    todo: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_todo = Todo(**todo.dict(), owner_id=current_user.id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    
    # Clear cache for this user
    cache.delete_pattern(f"todos_user_{current_user.id}_*")
    
    return db_todo

@app.put("/todos/{todo_id}", response_model=TodoSchema)
def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == current_user.id).first()
    if not db_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    # Update fields
    update_data = todo_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_todo, field, value)
    
    db_todo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_todo)
    
    # Clear cache for this user
    cache.delete_pattern(f"todos_user_{current_user.id}_*")
    
    return db_todo

@app.delete("/todos/{todo_id}")
def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == current_user.id).first()
    if not db_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found"
        )
    
    db.delete(db_todo)
    db.commit()
    
    # Clear cache for this user
    cache.delete_pattern(f"todos_user_{current_user.id}_*")
    
    return {"message": "Todo deleted successfully"}

@app.get("/")
def root():
    return {"message": "MyTodo API is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)