from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Subscribe, User
from api.pagination import PageNumberLimitPagination
from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminAuthorOrReadOnly, IsAdminOrReadOnly
from api.serializers import (
    CreateRecipeSerializer,
    ShoppingCartSerializer,
    CustomUserSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    SubscribeSerializer,
    FavoriteSerializer,
    TagSerializer,
)
from recipes.models import (
    IngredientRecipe,
    ShoppingCart,
    Ingredient,
    Favorite,
    Recipe,
    Tag
)


# class CustomUserViewSet(UserViewSet):
#     queryset = User.objects.all()
#     serializer_class = CustomUserSerializer
#     pagination_class = PageNumberLimitPagination
#     lookup_field = 'id'

#     @action(
#         detail=True,
#         methods=['post', 'delete'],
#         permission_classes=[IsAuthenticated]
#     )
#     def subscribe(self, request, **kwargs):
#         user = request.user
#         author_id = self.kwargs.get('id')
#         author = get_object_or_404(User, id=author_id)

#         if request.method == 'POST':
#             serializer = FollowSerializer(
#                 author,
#                 data=request.data,
#                 context={"request": request}
#             )
#             serializer.is_valid(raise_exception=True)
#             Follow.objects.create(user=user, author=author)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)

#         if request.method == 'DELETE':
#             subscription = get_object_or_404(
#                 Follow,
#                 user=user,
#                 author=author
#             )
#             subscription.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)

#     @action(
#         detail=False,
#         permission_classes=[IsAuthenticated]
#     )
#     def subscriptions(self, request):
#         user = request.user
#         queryset = User.objects.filter(subscribing__user=user)
#         pages = self.paginate_queryset(queryset)
#         serializer = FollowSerializer(
#             pages,
#             many=True,
#             context={'request': request}
#         )
#         return self.get_paginated_response(serializer.data)

class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    lookup_field = 'id'

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            # if user == author:
            #     return Response({
            #         'errors': 'Вы не можете подписываться на самого себя'
            #     }, status=status.HTTP_400_BAD_REQUEST)
            if Subscribe.objects.filter(user=user, author=author).exists():
                return Response({
                    'errors': 'Вы уже подписаны на данного пользователя'
                }, status=status.HTTP_400_BAD_REQUEST)
            follow = Subscribe.objects.create(user=user, author=author)
            serializer = SubscribeSerializer(
                follow, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            subscription = get_object_or_404(
                Subscribe,
                user=user,
                author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = Subscribe.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = CreateRecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAdminAuthorOrReadOnly,)
    pagination_class = PageNumberLimitPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return CreateRecipeSerializer

    @staticmethod
    def send_txt(ingredients):
        shopping_list = 'Купить в магазине:'
        for ingredient in ingredients:
            shopping_list += (
                f"\n{ingredient['ingredient__name']} "
                f"({ingredient['ingredient__measurement_unit']}) - "
                f"{ingredient['amount']}")
        file = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file}.txt"'
        return response

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).order_by('ingredient__name').values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        return self.send_txt(ingredients)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        context = {'request': request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'recipe': recipe.id,
            'user': request.user.id
        }
        serializer = ShoppingCartSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        get_object_or_404(
            ShoppingCart,
            recipe=get_object_or_404(Recipe, id=pk),
            user=request.user.id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('POST',),
        permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        context = {"request": request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'recipe': recipe.id,
            'user': request.user.id
        }
        serializer = FavoriteSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        get_object_or_404(
            Favorite,
            recipe=get_object_or_404(Recipe, id=pk),
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None
