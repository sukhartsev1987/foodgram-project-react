from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug',
                                             queryset=Tag.objects.all(),
                                             to_field_name='slug')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'tags', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        return queryset.filter(is_favorited=value)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return queryset.filter(is_in_shopping_cart=value)


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'
    lookup_expr = 'icontains'
