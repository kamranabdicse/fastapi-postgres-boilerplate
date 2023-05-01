<h1 style="text-align: center;">Cache</h1>

Basically, we should set the cache in the places where we are going to fetch (read) static data from the database and put it on the requests that will not change any data towards the database.
Of course, we can also use cache when changing data, which will depend on how our program works.
In these cases, the cached keys should be deleted so that our cache is not filled for each request from different users.

## Install
Redis is one of the best in-memory databases that we can use for caching.

1. To add Redis to the fastapi project, it is better to use the aioredis package, which is designed based on the requirements of asyncio.
Add it to the project with the following command:

```bash
poetry add aioredis
```

2. Add the cache module to the project.

3. Add Redis settings in the .env file of the project:

```
REDIS_SERVER=   # default: redis
REDIS_PORT=     # default: 6379
REDIS_PASSWORD= # your password to authenticate in redis database
```

And then adding these variables to setting:

```python
# core/config.py

REDIS_SERVER: str
REDIS_PORT: int
REDIS_PASSWORD: str
REDIS_TIMEOUT: Optional[int] = 5
```

4. To connect to Redis, it is better to call the init function in the main.py file of the project, which is responsible for connecting to the database; The reason for this is that we can connect to Redis every time we run our project.

```python
# app/main.py

from cache import Cache

@app.on_event("startup")
async def startup():
    redis_cache = Cache()
    url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_SERVER}:{settings.REDIS_PORT}"
    await redis_cache.init(
        host_url=url,
        prefix="api-cache",
        response_header="X-API-Cache",
        ignore_arg_types=[Request, Response, Session, AsyncSession, User],
    )
```

The app.event('startup') function is actually a decorator that specifies that the written function should be called every time the application is launched.

The redis_cache value is an instance of the cache class.

The url variable will specify the path to connect to the database, which will read the required data such as password, port and server from the .env file.

The starting point for connecting to the database is redis_cache.init, which accepts the following parameters:

The database address is specified by __host_url__.

The __prefix__ contains an arbitrary value that is placed at the beginning of the name of each key.

To control the cache in the browser, which is set in every request and response, we use the __response_header__.

In general, some data should not be cached in the system because some may be unique or very repetitive and fill the cache memory.
Things like users, database sessions, requests and responses should not be cached in __ignore_arg_types__. Also, in models where a unique object is created in memory for each request, we can prevent each object from being cached by presenting the model in the __str__ or __repr__ functions.

For example, if you don't present your model with the mentioned functions, the keys in the database will be as follows with each request:

```bash
# redis keys

"api-cache|user-cache:app.api.api_v1.endpoints.users.read_user_by_id(user_id=1,current_user=<app.models.user.User object at 0x7f97b82eada0>)"
"api-cache|user-cache:app.api.api_v1.endpoints.users.read_user_by_id(user_id=1,current_user=<app.models.user.User object at 0x7g69b82scdk9>)"
"api-cache|user-cache:app.api.api_v1.endpoints.users.read_user_by_id(user_id=1,current_user=<app.models.user.User object at 0x6b37t15wllr3>)"
"api-cache|user-cache:app.api.api_v1.endpoints.users.read_user_by_id(user_id=1,current_user=<app.models.user.User object at 0x1b64c98trnh2>)"
```


## Use in endpoints
5. To use, we must first enter the cache and invalidate functions from the Cache module:

```python
from cache import cache, invalidate
```

To keep the cached data in the database, we can use the times defined in the module.
These times include one hour, one day, one week, one month and one year. You can also enter your desired time in integer.
For example, here we enter the time of a day:

```python
from cache.util import ONE_DAY_IN_SECONDS
```

6. Set namespace:
With the help of namespace we can find out which module the cached keys belong to. For example, by setting it in the user module, all the cached keys of this module will have the word "user-cache" at the beginning of their name.

```python
namespace = 'user-cache'
```

7. To cache the desired endpoint requests, we use the cache decorator on it.
This decorator takes two main parameters:
* The namespace value we set in the previous step.
* Cache expiration time, which can be integer value for any time.

After this decorator is set, the data will be stored in the cache for each request from the user, which will speed up the response.
For example, you can see the endpoint of users below:

__Tip__: Cache decorator must be under our router.

```python
# api/api_v1/endpoints/users.py

@router.get("/", response_model=List[schemas.User])
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_users(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return users
```

Instead of using the cache decorator, you can also use time decorators, for example:

```python
# api/api_v1/endpoints/users.py

from cache import ONE_DAY_IN_SECONDS

@router.get("/", response_model=List[schemas.User])
@ONE_DAY_IN_SECONDS(namespace=namespace)
async def read_users(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return users
```

After sending the request, the cached keys will be as follows:

```bash
# redis keys

"api-cache|user-cache:app.api.api_v1.endpoints.users.read_users(skip=0,limit=100)"
"api-cache|user-cache:app.api.api_v1.endpoints.users.login_access_token(form_data=<fastapi.security.oauth2.OAuth2PasswordRequestForm object at 0x7f940f6693c0>)"
```

8. Clearing caches: It was explained at the beginning that for create or update requests that change data on the database side, it is better not to cache because this data is not the same for each request and only fills the cache.
In these endpoints, we use invalidate so that for each data change, all caches of the corresponding module are cleared and cached from the beginning with new data.

This function takes only the value of the namespace as a parameter to clear the caches related to the same namespace.

The efficiency of this function can be seen in the creation of a new user:

```python
# api/api_v1/endpoints/users.py

@router.post("/", response_model=schemas.User)
@invalidate(namespace=namespace)
async def create_user(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user = await crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = await crud.user.create(db, obj_in=user_in)
    return user
```

## Important Points

### Response types
1. Since the fastapi response cannot be serialized or converted to json, we have to get the response body to handle it. If our response is something other than an instance of the Response model, for example, if it is text, we must serialize it using the serialize_json function.

```python
# cache/client.py | add_to_cache function

if isinstance(value, Response):
    response_data = value.body
else:
    response_data = serialize_json(value)
```

2. Regarding media caching, since Redis database cannot have a key other than string, we cannot cache them directly. Now, to do this, we can first cache the base64 image or file and then stream it. Like the following sample code:

```python
@cache(namespace="image", expire=ONE_HOUR_IN_SECONDS)
async def read_image_base64(db: AsyncSession, image_id: int):
    image = await crud.image.get(db=db, id=image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    image = jsonable_encoder(image)
    return image
```
