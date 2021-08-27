from django.contrib import admin
from django.db import models
from pdb import set_trace
from django.conf import settings
from django.urls import reverse


DEFAULT_STATUS = "Ej Påbörjad"

STATUS_VAL = (('Avråds', "Avråds"),
              ('Beslutad', 'Beslutad'), 
              ('Definiera ej', 'Definiera ej'), 
              ('För validering', 'För validering'), 
              ("Internremiss", "Internremiss"),
              ('Preliminär', 'Preliminär'),
              ('Publicera ej', 'Publicera ej'),
              ('Pågår', 'Pågår'), 
              ("Önskad Översättning","Önskad Översättning"),
              ("Översättning", "Översättning"),
              (DEFAULT_STATUS, DEFAULT_STATUS))

SYSTEM_VAL = (('Millennium', "Millennium"),
              ('Annat system', "Annat system"),
               ('VGR Begreppsystem',"VGR Begreppsystem"))
            

class Begrepp(models.Model):

    class Meta:
        verbose_name_plural = "Begrepp"

    begrepp_kontext = models.TextField(default='Inte definierad')
    begrepp_version_nummer = models.DateTimeField(auto_now=True, verbose_name='Senaste ändring')
    datum_skapat = models.DateTimeField(auto_now_add=True, verbose_name='Datum skapat')
    beställare = models.ForeignKey('Bestallare', to_field='id', on_delete=models.CASCADE)
    definition = models.TextField(blank=True)
    alternativ_definition = models.TextField(blank=True, null=True)
    externt_id = models.CharField(max_length=255, null=True, default='Inte definierad', verbose_name="Kod")
    källa = models.CharField(max_length=255, null=True, default='Inte definierad')
    annan_ordlista = models.CharField(max_length=255, null=True, default='Inte definierad')
    status = models.CharField(max_length=255, choices=STATUS_VAL, default=DEFAULT_STATUS)
    term = models.CharField(max_length=255, default='Angavs ej')
    utländsk_term = models.CharField(max_length=255, blank=True)
    utländsk_definition = models.TextField(default='Inte definierad')
    id_vgr = models.CharField(max_length=255, null=True, default='Inte definierad')
    anmärkningar = models.TextField(null=True, default='Inte definierad')
    kommentar_handläggning = models.TextField(null=True, default='Inte definierad')
    term_i_system = models.CharField(verbose_name="Används i system",max_length=255,blank=True,null=True, choices=SYSTEM_VAL)
    email_extra = models.TextField(null=True, blank=True)
    

    def __str__(self):
        return self.term

    def get_absolute_url(self):
        """Returns the url to access a particular instance of the model."""
        return reverse('begrepp_förklaring', kwargs={'begrepp_id' : str(self.id)})

class BegreppExternalFiles(models.Model):
    begrepp = models.ForeignKey("Begrepp", to_field='id', on_delete=models.CASCADE)
    support_file = models.FileField(blank=True, null=True, upload_to='')

    def __str__(self):
        return str(self.support_file)

class Bestallare(models.Model):
    class Meta:
        verbose_name_plural = "Beställare"

    beställare_namn = models.CharField(max_length=255, blank=True)
    beställare_datum = models.DateTimeField(auto_now_add=True)
    önskad_slutdatum = models.DateTimeField(null=True, blank=True)
    beställare_email = models.EmailField()
    beställare_telefon = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.beställare_namn

class Doman(models.Model):
    class Meta:     
        verbose_name_plural = "Domäner"

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.CASCADE, blank=True, null=True, related_name='begrepp_fk')
    domän_id = models.AutoField(primary_key=True)
    domän_kontext = models.TextField(blank=True, null=True)
    domän_namn = models.CharField(max_length=255)       

    def __str__(self):
        return self.domän_namn

class Synonym(models.Model):

    SYNONYM_STATUS =  (('Avråds', "Avråds"),
                       ('Tillåten', "Tillåten"),
                       ('Rekommenderad', "Rekommenderad"),
                       ('Inte angiven','Inte angiven'))

    class Meta:
        verbose_name_plural = "Synonymer"

    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.CASCADE, blank=True, null=True)
    synonym = models.CharField(max_length=255, blank=True, null=True)
    synonym_status = models.CharField(max_length=255, choices=SYNONYM_STATUS, default='Inte angiven')

    def __str__(self):
        return self.synonym

class OpponeraBegreppDefinition(models.Model):

    class Meta:
        verbose_name_plural = 'Kommenterade Begrepp'
    
    begrepp = models.ForeignKey("Begrepp", to_field="id", on_delete=models.CASCADE, blank=True, null=True)
    begrepp_kontext = models.TextField()
    datum = models.DateTimeField(auto_now_add=True)
    epost = models.EmailField()
    namn = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_VAL, default=DEFAULT_STATUS)
    telefon = models.CharField(max_length=30)

class SökData(models.Model):

    class Meta:
        verbose_name_plural = 'Sök data'

    sök_term = models.CharField(max_length=255)
    ip_adress = models.GenericIPAddressField()
    sök_timestamp = models.DateTimeField(auto_now_add=True)
    records_returned = models.TextField()

    def __str__(self):
        return self.sök_term

class SökFörklaring(models.Model):

    class Meta:
        verbose_name = ('Sök Förklaring')

    sök_term = models.CharField(max_length=255)
    ip_adress = models.GenericIPAddressField()
    sök_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sök_term
    
