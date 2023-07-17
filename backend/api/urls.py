from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, UserViewSet, TagViewSet

app_name = 'api'

route_v1 = DefaultRouter()

route_v1.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients'
)
route_v1.register(
    r'recipes',
    RecipeViewSet,
    basename='recipes'
)
route_v1.register(
    r'users',
    UserViewSet,
    basename='users'
)
route_v1.register(
    r'tags',
    TagViewSet,
    basename='tags'
)


urlpatterns = [
    path('', include(route_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
