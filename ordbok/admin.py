from ordbok.forms import BegreppForm
from pdb import set_trace
from django.urls import reverse
from django.db.models.functions import Lower
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.html import format_html
import django.utils.encoding
from django.db.models import Q, Case, When, Value, IntegerField
from django.db.models import F, IntegerField, TextField, Value
from django.db.models.functions import Cast, StrIndex, Substr

from django.contrib import admin
from ordbok.models import *
from .functions import skicka_epost_till_beställaren_beslutad
from .functions import skicka_epost_till_beställaren_status
from .functions import skicka_epost_till_beställaren_validate
from .functions import ändra_status_till_översättning
from django import forms
import re

admin.site.site_header = "OLLI Begreppstjänst Admin - För fakta i livet"
admin.site.site_title = "OLLI Begpreppstjänst Admin Portal"
admin.site.index_title = "Välkommen till OLLI Begreppstjänst Portalen"

def add_non_breaking_space_to_status(status_item):

    length = len(status_item)
    length_to_add = 12 - length
    for x in range(length_to_add):
        if x % 2 == 0:
            status_item += '&nbsp;'
        else:
            status_item = '&nbsp;' + status_item
    return mark_safe(status_item)

class SynonymInlineForm(forms.ModelForm):

    class Meta:
        model = Synonym
        fields = "__all__"

    def clean(self):
        super(SynonymInlineForm, self).clean()
        if self.cleaned_data.get('synonym') == None:
            self.add_error('synonym', 'Kan inte radera synonym med bak knappen, använder checkbox till höger')

class SynonymInline(admin.StackedInline):

    model = Synonym
    form = SynonymInlineForm
    extra = 1

class BegreppExternalFilesInline(admin.StackedInline):

    model = BegreppExternalFiles
    extra = 1
    verbose_name = "Externt Kontext Fil"
    verbose_name_plural = "Externa Kontext Filer"

class ValideradAvDomänerInline(admin.StackedInline):
    
    model = Doman
    extra = 1
    verbose_name = "Validerad av"
    verbose_name_plural = "Validerad av"
    exclude = ['domän_kontext']

class BegreppSearchResultsAdminMixin(object):

    def get_search_results(self, request, queryset, search_term):
    
        ''' Show exact match for title at top of admin search results.
        '''
    
        qs, use_distinct = \
            super(BegreppSearchResultsAdminMixin, self).get_search_results(
                request, queryset, search_term)
        
        search_term = search_term.strip()
        if not search_term:
            return qs, use_distinct

        qs = qs.annotate(
            position=Case(
                When(Q(term__iexact=search_term), then=Value(1)),
                When(Q(term__istartswith=search_term), then=Value(2)),
                When(Q(term__icontains=search_term), then=Value(3)), 
                When(Q(synonym__synonym__icontains=search_term), then=Value(4)), 
                When(Q(utländsk_term__icontains=search_term), then=Value(5)),
                When(Q(definition__icontains=search_term), then=Value(6)), 
                default=Value(6), output_field=IntegerField()
            )
        )

        order_by = []
        if qs.filter(position=1).exists():
            order_by.append('position')

        if order_by:
            qs = qs.order_by(*order_by)

        return qs, use_distinct


class BegreppAdmin(BegreppSearchResultsAdminMixin, admin.ModelAdmin):

    class Media:
        css = {
        'all': (f'{settings.STATIC_URL}css/main.css',
                f'{settings.STATIC_URL}css/begrepp_custom.css',
               )
         }
    
    inlines = [BegreppExternalFilesInline, SynonymInline, ValideradAvDomänerInline]

    change_form_template = 'change_form_autocomplete.html'

    form = BegreppForm

    view_on_site = True

    fieldsets = [
        ['Main', {
        'fields': [('datum_skapat','begrepp_version_nummer'), ('status', 'id_vgr',)],
        }],
        [None, {
        #'classes': ['collapse'],
        'fields' : ['term',
                    'definition',
                    'källa',
                    'alternativ_definition',
                    'anmärkningar',
                    'utländsk_term',
                    'utländsk_definition',
                    'term_i_system',
                    'email_extra',
                    ('annan_ordlista', 'externt_id'),
                    ('begrepp_kontext'),
                    ('beställare','beställare__beställare_epost'),
                    'kommentar_handläggning']
        }]
    ]

    list_display_links = ('term',)

    readonly_fields = ['begrepp_version_nummer','datum_skapat','beställare__beställare_epost']

    def beställare__beställare_epost(self, obj):
        return obj.beställare.beställare_email

    save_on_top = True

    list_display = ('id',
                    'term',
                    'synonym',
                    'definition',
                    'utländsk_term',
                    'get_domäner',
                    'status_button',
                    #'visa_html_i_begrepp_kontext',    
                    'annan_ordlista',
                    'begrepp_version_nummer',
                    'beställare',
                    'önskad_slutdatum')

    list_filter = ("begrepp_version_nummer", "status",)

    search_fields = ('term',
                    'definition',
                    'begrepp_kontext',    
                    'annan_ordlista',
                    'utländsk_definition',
                    'utländsk_term',
                    'synonym__synonym')

    date_hierarchy = 'begrepp_version_nummer'

    actions = ['skicka_epost_till_beställaren_beslutad','skicka_epost_till_beställaren_status','skicka_epost_till_beställaren_validate', 'ändra_status_översättning']

    def skicka_epost_till_beställaren_beslutad(self, request, queryset):
        skicka_epost_till_beställaren_beslutad(queryset)
        self.message_user(request, 'Mail skickat till beställaren.')
    skicka_epost_till_beställaren_beslutad.short_description = "Skicka epost till beställaren: Beslutat"

    
    def skicka_epost_till_beställaren_status(self, request, queryset):
        skicka_epost_till_beställaren_status(queryset)
        self.message_user(request, 'Mail skickat till beställaren.')
    skicka_epost_till_beställaren_status.short_description = "Skicka epost till beställaren: Status"

    def skicka_epost_till_beställaren_validate(self, request, queryset):
        skicka_epost_till_beställaren_validate(queryset)
        self.message_user(request, 'Mail skickat till beställaren.')
    skicka_epost_till_beställaren_validate.short_description = "Skicka epost till beställaren: Validera"

    def ändra_status_översättning(self, request, queryset):
        ändra_status_till_översättning(queryset)
        
    ändra_status_översättning.short_description = "Ändra status -> Översättning"

    def önskad_slutdatum(self, obj):
        
        return obj.beställare.önskad_slutdatum

    def synonym(self, obj):
        
        display_text = ", ".join([
            "<a href={}>{}</a>".format(
                    reverse('admin:{}_{}_change'.format(obj._meta.app_label,  obj._meta.related_objects[2].name),
                    args=(synonym.id,)),
                synonym.synonym)
             for synonym in obj.synonym_set.all()
        ])
        if display_text:
            return mark_safe(display_text)
        return "-"

    def get_queryset(self, obj):
        qs = super(BegreppAdmin, self).get_queryset(obj)
        return qs.prefetch_related('begrepp_fk')

    def get_domäner(self, obj):
        domäner = Doman.objects.filter(begrepp_id=obj.pk)
        return list(domäner)

    get_domäner.short_description = 'Validerad av'


    
    # def visa_html_i_begrepp_kontext(self, obj):
        
    #     set_trace()
    #     if len(re.findall("|") > 1:
    #     if ("|" in obj.begrepp_kontext) and ('http' in obj.begrepp_kontext):
    #         set_trace()
    #         description, url = obj.begrepp_kontext.split('|')

    #         display_text = f"<a href={url}>{description}</a>"
    #         return mark_safe(display_text)
    #     else:
    #     return obj.begrepp_kontext

    # visa_html_i_begrepp_kontext.short_description = "begrepp context"
    
    def status_button(self, obj):

        if (obj.status == 'Avråds') or (obj.status == 'Avrådd'):
            display_text = f'<button class="btn-xs btn-avrådd text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Publicera ej'):
            display_text = f'<button class="btn-xs btn-light-blue text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Pågår') or (obj.status == 'Ej Påbörjad'):
            display_text = f'<button class="btn-xs btn-oklart text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Preliminär'):
            display_text = f'<button class="btn-xs btn-gul text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Översättning'):
            display_text = f'<button class="btn-xs btn-översättning text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        elif (obj.status == 'Beslutad'):
            display_text = f'<button class="btn-xs btn-grön text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        else:
            display_text = f'<button class="btn-xs btn-white text-monospace">{add_non_breaking_space_to_status(obj.status)}</button>'
        return mark_safe(display_text)

    status_button.short_description = 'Status'

    # def save_model(self, request, obj, form, change):
    #     if "http" in obj.begrepp_kontext:
    #         obj.begrepp_kontext = f"<a href={obj.begrepp_kontext}>SCT{obj.begrepp_kontext.split('/')[-1]}</a>"           
    #     super().save_model(request, obj, form, change)

class BestallareAdmin(admin.ModelAdmin):

    list_display = ('beställare_namn',
                    'beställare_email',
                    'beställare_telefon',
                    'beställare_datum',
                    'önskad_slutdatum',
                    'begrepp')
    search_fields = ("begrepp__term","beställare_namn", "beställare_email") 

    def begrepp(self, obj):
        # set_trace()
        display_text = ", ".join([
            "<a href={}>{}</a>".format(
                    reverse('admin:{}_{}_change'.format(obj._meta.app_label,  obj._meta.related_objects[0].name),
                    args=(begrepp.id,)),
                begrepp.term)
             for begrepp in obj.begrepp_set.all()
        ])
        if display_text:
            return mark_safe(display_text)
        return display_text

class DomanAdmin(admin.ModelAdmin):

    list_display = ('domän_namn',
                    'domän_id',
                    'domän_kontext',
                    'begrepp',)

    list_select_related = (
        'begrepp',
    )

    list_filter = ("domän_namn",)
    search_fields = ('begrepp__term',)

class SynonymAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "begrepp":
            kwargs["queryset"] = Begrepp.objects.filter().order_by(Lower('term'))
        return super(SynonymAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    ordering = ['begrepp__term']
    list_display = ('begrepp',
                    'synonym',
                    'synonym_status')

    list_select_related = (
        'begrepp',
    )
    list_filter = ("synonym_status",)
    search_fields = ("begrepp__term", "synonym")

class OpponeraBegreppDefinitionAdmin(admin.ModelAdmin):

    class Media:
        css = {
            'all': (f'{settings.STATIC_URL}css/admin_kommentarmodel_custom.css',)
            }

    list_display = ('begrepp',
                    'begrepp_kontext',
                    'datum',
                    'epost',
                    'namn',
                    'status',
                    'telefon')

    list_filter = ('status',)

class SökFörklaringAdmin(admin.ModelAdmin):

    list_display = ('sök_term',
                    'ip_adress',
                    'sök_timestamp')

class SökDataAdmin(admin.ModelAdmin):

    list_display = ('sök_term',
                    'ip_adress',
                    'sök_timestamp',
                    'records_returned')



admin.site.register(Begrepp, BegreppAdmin)
admin.site.register(Bestallare, BestallareAdmin)
admin.site.register(Doman, DomanAdmin)
admin.site.register(Synonym, SynonymAdmin)
admin.site.register(OpponeraBegreppDefinition, OpponeraBegreppDefinitionAdmin)
admin.site.register(SökFörklaring, SökFörklaringAdmin)
admin.site.register(SökData, SökDataAdmin)
admin.site.register(BegreppExternalFiles)