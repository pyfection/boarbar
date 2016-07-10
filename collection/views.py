

from django.shortcuts import render

from .models import CollectionItem


def collection_view(request):
    songs = CollectionItem.objects.filter(kind='song')
    tongue_twisters = CollectionItem.objects.filter(kind='tongue_twister')
    sayings = CollectionItem.objects.filter(kind='saying')
    poems = CollectionItem.objects.filter(kind='poem')
    kwargs = {
        'songs': songs,
        'tongue_twisters': tongue_twisters,
        'sayings': sayings,
        'poems': poems,
    }
    return render(request, 'collection/main.html', kwargs)