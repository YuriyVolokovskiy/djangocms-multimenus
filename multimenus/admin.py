from django.conf import settings
from django.contrib import admin
from django.contrib.sites.shortcuts import get_current_site
from django.forms import widgets
from django.utils.encoding import force_str
from django.utils.translation import gettext, gettext_lazy as _

from cms.utils.i18n import get_current_language
from cms.utils.urlutils import admin_reverse

from parler.admin import TranslatableAdmin
from treebeard.admin import TreeAdmin

from .forms import MenuItemAdminForm
from .models import MenuItem


class AllTranslationsMixin(object):

    @property
    def media(self):
        return super(AllTranslationsMixin, self).media + widgets.Media(
            css={'all': ('css/admin/all-translations-mixin.css',), }
        )

    def all_translations(self, obj):
        """
        Adds a property to the list_display that lists all translations with
        links directly to their change forms. Includes CSS to style the links
        to looks like tags with color indicating current language, active and
        inactive translations.

        A similar capability is in HVAD, and now there is this for
        Parler-based projects.
        """
        available = list(obj.get_available_languages())
        current = get_current_language()
        langs = []
        for code, lang_name in settings.LANGUAGES:
            classes = ["lang-code", ]
            title = force_str(lang_name)
            if code == current:
                classes += ["current", ]
            if code in available:
                classes += ["active", ]
                title += " (translated)"
            else:
                title += " (untranslated)"
            change_form_url = admin_reverse(
                '{app_label}_{model_name}_change'.format(
                    app_label=obj._meta.app_label.lower(),
                    model_name=obj.__class__.__name__.lower(),
                ), args=(obj.id,)
            )
            link = '<a class="{classes}" href="{url}?language={code}" title="{title}">{code}</a>'.format(
                classes=' '.join(classes),
                url=change_form_url,
                code=code,
                title=title,
            )
            langs.append(link)
        return ''.join(langs)

    all_translations.short_description = 'Translations'
    all_translations.allow_tags = True

    def get_list_display(self, request):
        """
        Unless the the developer has already placed "all_translations" in the
        list_display list (presumably specifically where she wants it), append
        the list of translations to the end.
        """
        list_display = super(
            AllTranslationsMixin, self).get_list_display(request)
        if 'all_translations' not in list_display:
            list_display = list(list_display) + ['all_translations', ]
        return list_display


@admin.register(MenuItem)
class MenuItemAdmin(AllTranslationsMixin, TranslatableAdmin, TreeAdmin):
    fieldsets = (
        (None, {'fields': ('title', 'menu_id')}),
        (_('Link'), {'fields': ('page', 'url', 'target', "is_highlighted")}),
        (_('Tree position'), {'fields': ('_position', '_ref_node_id')}),
    )
    form = MenuItemAdminForm
    list_display = ('title', 'menu_id',)
    ordering = ('path',)
    search_fields = ('translations__title', 'menu_id',)

    def get_form(self, request, obj=None, **kwargs):
        form_cls = super().get_form(request, obj, **kwargs)
        form_cls.base_fields['_position'].label = gettext('Position')
        form_cls.base_fields['_ref_node_id'].label = gettext('Relative to')
        return form_cls

    def get_queryset(self, request):
        current_site = get_current_site(request)
        return super().get_queryset(request).filter(site=current_site)

    def save_model(self, request, obj, form, change):
        current_site = get_current_site(request)
        obj.site = current_site
        return super().save_model(request, obj, form, change)
