# from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.models import Follow, User
from recipes.models import (
    IngredientRecipe,
    ShoppingCart,
    Ingredient,
    Favorite,
    Recipe,
    Tag
)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'is_subscribed',
            'first_name',
            'username',
            'last_name',
            'email',
            'id'
        )
        model = User
        lookup_field = 'username'

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj.id).exists()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'password',
            'email',
            'id'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'username': {'required': True},
            'password': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'cooking_time',
            'image',
            'name',
            'id'
        )
        read_only_fields = (
            'cooking_time',
            'image',
            'name',
            'id'
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = (
            'color',
            'name',
            'slug',
            'id'
        )


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'measurement_unit',
            'name',
            'id'
        )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='ingredient.name')
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'measurement_unit',
            'amount',
            'name',
            'id'
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientRecipeSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        error_messages={'does_not_exist': 'Такого тега не существует'}
    )
    image = Base64ImageField(max_length=None)
    author = CustomUserSerializer(read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'cooking_time',
            'ingredients',
            'author',
            'image',
            'name',
            'text',
            'tags',
            'id'
        )

    def create_ingredients(self, recipe, ingredients):
        ingredient_list = [
            IngredientRecipe(
                ingredient=ingredient_data.pop("id"),
                amount=ingredient_data.pop("amount"),
                recipe=recipe,
            )
            for ingredient_data in ingredients
        ]
        IngredientRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags")
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.create_ingredients(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    # ingredients = IngredientRecipeSerializer(
    #     many=True,
    # )
    # tags = serializers.PrimaryKeyRelatedField(
    #     many=True,
    #     queryset=Tag.objects.all(),
    #     error_messages={'does_not_exist': 'Такого тега не существует'}
    # )
    # image = Base64ImageField(max_length=None)
    # author = CustomUserSerializer(read_only=True)
    # cooking_time = serializers.IntegerField()

    # class Meta:
    #     model = Recipe
    #     fields = (
    #         'cooking_time',
    #         'ingredients',
    #         'author',
    #         'image',
    #         'name',
    #         'text',
    #         'tags',
    #         'id'
    #     )

    # @transaction.atomic
    # def create_ingredients(self, recipe, ingredients):
    #     ingredient_liist = []
    #     for ingredient_data in ingredients:
    #         ingredient_liist.append(
    #             IngredientRecipe(
    #                 ingredient=ingredient_data.pop('id'),
    #                 amount=ingredient_data.pop('amount'),
    #                 recipe=recipe,
    #             )
    #         )
    #     IngredientRecipe.objects.bulk_create(ingredient_liist)

    # @transaction.atomic
    # def create(self, validated_data):
    #     request = self.context.get('request', None)
    #     ingredients = validated_data.pop('ingredients')
    #     tags = validated_data.pop('tags')
    #     recipe = Recipe.objects.create(author=request.user, **validated_data)
    #     recipe.tags.set(tags)
    #     self.create_ingredients(recipe, ingredients)
    #     return recipe

    # @transaction.atomic
    # def update(self, instance, validated_data):
    #     tags = validated_data.pop('tags')
    #     ingredients = validated_data.pop('ingredients')
    #     instance = super().update(instance, validated_data)
    #     instance.tags.clear()
    #     instance.tags.set(tags)
    #     instance.ingredients.clear()
    #     self.create_ingredients(
    #         recipe=instance,
    #         ingredients=ingredients
    #     )
    #     instance.save()
    #     return instance

    # def to_representation(self, instance):
    #     return RecipeReadSerializer(instance, context={
    #         'request': self.context.get('request')
    #     }).data


class RecipeReadSerializer(serializers.ModelSerializer):
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    author = CustomUserSerializer(read_only=True, many=False)
    tags = TagSerializer(read_only=False, many=True)
    image = Base64ImageField(max_length=None)
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredienttorecipe'
    )

    class Meta:
        model = Recipe
        fields = (
            'is_in_shopping_cart',
            'cooking_time',
            'is_favorited',
            'ingredients',
            'author',
            'image',
            'name',
            'text',
            'tags',
            'id'
        )

    def get_ingredients(self, obj):
        ingredients = IngredientRecipe.objects.filter(recipe=obj)
        return IngredientRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.shopping_list.filter(user=request.user).exists()


class FollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    username = serializers.ReadOnlyField(source='author.username')
    recipes = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')

    class Meta:
        model = Follow
        fields = (
            'is_subscribed',
            'recipes_count',
            'first_name',
            'last_name',
            'username',
            'recipes',
            'email',
            'id'
        )

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=obj.user, author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data

    def validate(self, data):
        user = data['user']
        if user.shopping_list.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже в корзине'
            )
        return data


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        if user.favorites.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
