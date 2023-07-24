from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.models import Follow, User
from api.pagination import PageNumberLimitPagination
from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminOrReadOnly
# , IsAuthorOrReadOnly
from api.serializers import (
    CreateRecipeSerializer,
    ShoppingCartSerializer,
    CustomUserSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    FavoriteSerializer,
    FollowSerializer,
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


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = PageNumberLimitPagination
    lookup_field = 'id'
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def subscribe_error_response(
        errors,
        status_code=status.HTTP_400_BAD_REQUEST
    ):
        return Response({'errors': errors}, status=status_code)

    def is_subscribed(self, user, author):
        return Follow.objects.filter(user=user, author=author).exists()

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            if user == author:
                return self.subscribe_error_response(
                    'Вы не можете подписываться на самого себя'
                )
            if self.is_subscribed(user, author):
                return self.subscribe_error_response(
                    'Вы уже подписаны на данного пользователя'
                )
            follow = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(follow, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            subscription = get_object_or_404(Follow, user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    # permission_classes = (IsAuthorOrReadOnly | IsAdminOrReadOnly,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CreateRecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageNumberLimitPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return CreateRecipeSerializer

    @staticmethod
    def create_list_of_products(ingredients):
        list_of_products = ["Купить в магазине:"]
        for ingredient in ingredients:
            ingredient_name = ingredient.get("ingredient__name", "")
            measurement_unit = ingredient.get(
                "ingredient__measurement_unit", ""
            )
            amount = ingredient.get("amount", "")
            list_of_products.append(
                f"{ingredient_name} ({measurement_unit}) - {amount}"
            )
        return "\n".join(list_of_products)

    @action(detail=False, methods=("GET",),)
    def download_shopping_cart(self, request):
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_list__user=request.user
        ).order_by("ingredient__name").values(
            "ingredient__name",
            "ingredient__measurement_unit"
        ).annotate(amount=Sum('amount'))
        shopping_list_content = self.create_list_of_products(ingredients)
        file_name = "list_of_products.txt"
        response = HttpResponse(
            shopping_list_content,
            content_type='text/plain'
        )
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response

    @action(detail=True, methods=("POST",))
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {"recipe": recipe.id, "user": request.user.id}
        serializer = ShoppingCartSerializer(
            data=data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        get_object_or_404(
            ShoppingCart,
            recipe__id=pk,
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("POST",),)
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {"recipe": recipe.id, "user": request.user.id}
        serializer = FavoriteSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # 
    @action(detail=True, methods=["DELETE"])
    def destroy_favorite(self, request, pk):
        get_object_or_404(
            Favorite,
            recipe=get_object_or_404(Recipe, id=pk),
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # @staticmethod
    # def send_txt(ingredients):
    #     shopping_list = ['Купить в магазине:']
    #     for ingredient in ingredients:
    #         ingredient_name = ingredient.get('ingredient__name', '')
    #         measurement_unit = ingredient.get(
    #             'ingredient__measurement_unit', ''
    #         )
    #         amount = ingredient.get('amount', '')
    #         shopping_list.append(
    #             f'{ingredient_name} ({measurement_unit}) - {amount}'
    #         )
    #     file_content = '\n'.join(shopping_list)
    #     file_name = 'shopping_list.txt'
    #     response = HttpResponse(file_content, content_type='text/plain')
    #     response['Content-Disposition'] = (
    #         f'attachment; filename="{file_name}.txt"'
    #     )
    #     return response

    # @action(detail=False, methods=('GET',))
    # def download_shopping_cart(self, request):
    #     ingredients = IngredientRecipe.objects.filter(
    #         recipe__shopping_list__user=request.user
    #     ).order_by('ingredient__name').values(
    #         'ingredient__name',
    #         'ingredient__measurement_unit'
    #     ).annotate(amount=Sum('amount'))
    #     return self.send_txt(ingredients)

    # @action(
    #     detail=True,
    #     methods=('POST',),
    #     permission_classes=(IsAuthenticated,)
    # )
    # def shopping_cart(self, request, pk):
    #     context = {'request': request}
    #     recipe = get_object_or_404(Recipe, id=pk)
    #     data = {
    #         'recipe': recipe.id,
    #         'user': request.user.id
    #     }
    #     serializer = ShoppingCartSerializer(data=data, context=context)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    # @shopping_cart.mapping.delete
    # def destroy_shopping_cart(self, request, pk):
    #     get_object_or_404(
    #         ShoppingCart,
    #         recipe=get_object_or_404(Recipe, id=pk),
    #         user=request.user.id
    #     ).delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(
    #     detail=True,
    #     methods=('POST',),
    #     permission_classes=(IsAuthenticated,)
    # )
    # def favorite(self, request, pk):
    #     context = {"request": request}
    #     recipe = get_object_or_404(Recipe, id=pk)
    #     data = {
    #         'recipe': recipe.id,
    #         'user': request.user.id
    #     }
    #     serializer = FavoriteSerializer(data=data, context=context)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)

    # @favorite.mapping.delete
    # def destroy_favorite(self, request, pk):
    #     get_object_or_404(
    #         Favorite,
    #         recipe=get_object_or_404(Recipe, id=pk),
    #         user=request.user
    #     ).delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (IsAdminOrReadOnly,)


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)
    permission_classes = (IsAdminOrReadOnly,)
