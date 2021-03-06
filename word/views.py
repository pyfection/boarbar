

import re
import logging

from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import DetailView, TemplateView, ListView
from django.views.generic.edit import UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .models import Word, Description, WordVersion, WordLocation, Tag
from .forms import WordForm, EditForm
from language.models import Language
from user.models import Profile, UserLanguage
from contribute.views import get_highest_language_proficiency

logger = logging.getLogger(__name__)


class WordView(DetailView):
    template_name = 'word/display.html'
    http_method_names = ['get']
    model = Word

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        default_desc = self.object.desc.filter(language__name=self.object.version.language)
        if not default_desc:
            # there is no desc of the same language as the word
            default_desc = [self.object.desc.first()]

        default_syn =self.object.synonyms.filter(version__language=self.object.version.language)
        if not default_syn:
            # there is no syn of the same language as the word
            default_syn = [self.object.synonyms.first()]

        context.update({
            'descriptions': self.object.desc.all(),
            'description_default': default_desc,
            'synonym_default': default_syn,
            'synonyms': self.object.synonyms.all(),
            'locations': self.object.locations.all(),
            'tags': self.object.tags.all(),
        })
        return context



@method_decorator(login_required, name='dispatch')
class SuggestView(TemplateView):
    """
    User story:
      Word: Kusko
      WordVersion: Quechua Ayacuchano where the word they use is Kusko
      Language: Quechua
    """
    template_name = 'word/suggest.html'
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        try:
            user_profile = Profile.objects.get(user=request.user)
        except TypeError:
            logger.info("user does not have profile")
        else:
            context = add_default_variant(context, user_profile)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all()
        context["synonyms"] = Word.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        word_obj = None
        if request.method == "POST" and "file" in request.FILES:
            form = WordForm(request.POST, request.FILES)
            if form.is_valid():
                word_obj = form.save(commit=False)
                word_obj.submitter = request.user.profile
                word_obj.audio = request.FILES["file"]
                word_obj.save()
            else:
                print("$" * 10, form.errors)

        word = request.POST.get('word')
        tags = request.POST.getlist('tags')
        ipa = request.POST.get('ipa')
        default_variant_str = request.POST.get('language')
        location = request.POST.get('location')
        synonyms = request.POST.getlist('synonyms')
        wiktionary_link = request.POST.get('wiktionary_link')

        desc_list = self.create_descriptions(request)

        language_object = Language.objects.get(default_variant=default_variant_str)

        # TODO: so far all word versions of a language can be associated with
        # TODO: only one variant (the language's own default variant)
        word_version = WordVersion.objects.filter(language=language_object)[0]

        if word_obj:
            word_obj.word = word
            word_obj.ipa = ipa
            word_obj.status = 'SUG'
            word_obj.version = word_version
            word_obj.wiktionary_link = wiktionary_link
            word_obj.save()
        else:
            word_obj = Word.objects.create(
                word=word,
                ipa=ipa,
                status='SUG',
                version=word_version,
                submitter=request.user.profile,
                wiktionary_link=wiktionary_link,
            )

        for desc in desc_list:
            word_obj.desc.add(desc)

        for tag in tags:
            tag_object, _ = Tag.objects.get_or_create(name=tag.lower())
            word_obj.tags.add(tag_object)

        for syn in synonyms:
            syn_object, _ = Word.objects.get_or_create(
                submitter=request.user.profile,
                word=syn.lower(),
            )
            word_obj.synonyms.add(syn_object)
        if location:
            location = WordLocation.objects.create(
                word=word_obj,
                place=location,
                submitter=request.user.profile,
            )

        url = reverse_lazy('word:word_view', kwargs={'pk': word_obj.id})
        return HttpResponseRedirect(url)

    def create_descriptions(self, request):
        """Generate list of description objects for one word,
        each description object is in a different language and contains both
        short and long description strings

        {
            'english': {'desc_short': 'short mouse', 'desc_long': 'long mouse'},
            'spanish': {'desc_short': 'raton corto', 'desc_long': 'raton largo'}
        }
        :param request: original django request
        :return: list of Description objects
        """
        descriptions = {}

        for key, value in request.POST.items():
            if not value:
                continue
            if key.startswith("desc_long") or key.startswith("desc_short"):
                key, language_string = key.rsplit("_", 1)
                try:
                    desc = descriptions[language_string]
                except KeyError:
                    language_obj = Language.objects.get(name=language_string)
                    desc = Description(language=language_obj)
                    descriptions[language_string] = desc

                # assign Description.short = value
                if key == "desc_short":
                    setattr(desc, "short", value)
                # assign Description.extended = value
                if key == "desc_long":
                    setattr(desc, "extended", value)

        # select the Description objects that are stored as values in the dict
        # descriptions
        descriptions_to_create = list(descriptions.values())

        return Description.objects.bulk_create(descriptions_to_create)


@method_decorator(login_required, name='dispatch')
class SuggestViewApi(SuggestView):
    http_method_names = ['get', 'post']

    def post(self, request, *args, **kwargs):
        word_obj = None
        if request.method == "POST" and "file" in request.FILES:
            form = WordForm(request.POST, request.FILES)
            if form.is_valid():
                word_obj = form.save(commit=False)
                word_obj.submitter = request.user.profile
                word_obj.audio = request.FILES["file"]
                word_obj.save()
            else:
                print("$" * 10, form.errors)

        word = request.POST.get('word')
        tags = request.POST.getlist('tags')
        ipa = request.POST.get('ipa')
        default_variant_str = request.POST.get('language')
        location = request.POST.get('location')
        synonyms = request.POST.getlist('synonyms')
        wiktionary_link = request.POST.get('wiktionary_link')

        desc_list = self.create_descriptions(request)

        language_object = Language.objects.get(default_variant=default_variant_str)

        # TODO: so far all word versions of a language can be associated with
        # TODO: only one variant (the language's own default variant)
        word_version = WordVersion.objects.filter(language=language_object)[0]

        if word_obj:
            word_obj.word = word
            word_obj.ipa = ipa
            word_obj.status = 'SUG'
            word_obj.version = word_version
            word_obj.wiktionary_link = wiktionary_link
            word_obj.save()
        else:
            word_obj = Word.objects.create(
                word=word,
                ipa=ipa,
                status='SUG',
                version=word_version,
                submitter=request.user.profile,
                wiktionary_link=wiktionary_link,
            )

        for desc in desc_list:
            word_obj.desc.add(desc)

        for tag in tags:
            tag_object, _ = Tag.objects.get_or_create(name=tag.lower())
            word_obj.tags.add(tag_object)

        for syn in synonyms:
            syn_object, _ = Word.objects.get_or_create(
                submitter=request.user.profile,
                word=syn.lower(),
            )
            word_obj.synonyms.add(syn_object)
        if location:
            location = WordLocation.objects.create(
                word=word_obj,
                place=location,
                submitter=request.user.profile,
            )
        return HttpResponse(word_obj.id)


def add_default_variant(context, user_profile):
    user_languages = UserLanguage.objects.filter(user=user_profile)
    user_moderator = False
    for user_language in user_languages:
        if user_language.is_moderator:
            user_moderator = True
            break
    context["user_moderator"] = user_moderator
    context["user_languages"] = user_languages
    default_variant = get_highest_language_proficiency(user_languages)
    context["default_variant"] = default_variant
    return context

def edit_word(request, pk):
    word = Word.objects.get(id=pk)
    user_profile = Profile.objects.get(user=request.user)
    default_variants = UserLanguage.objects.filter(user=user_profile) \
        .values("language__default_variant", "language_id")
    user_languages = UserLanguage.objects.filter(user=user_profile)
    user_moderator = False
    word_language = word.version.language.name

    descriptions = word.desc.all()

    for user_language in user_languages:
        if user_language.language.name == word_language:
            if user_language.is_moderator:
                user_moderator = True
                break

    form = EditForm(request.POST or None)
    if form.is_valid():
        print("POST", request.POST)
        tags = request.POST.getlist("tags")
        word.tags.clear()
        for tag_str in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_str)
            word.tags.add(tag)

        word.synonyms.clear()
        for synonym in form.cleaned_data["synonyms"]:
            word.synonyms.add(synonym)

        update_descriptions(request, word)

        word.word = form.cleaned_data["word"]
        word.ipa = form.cleaned_data["ipa"]
        word.wiktionary_link = form.cleaned_data["wiktionary_link"]
        if request.FILES and "audio" in request.FILES:
            word.audio = request.FILES["audio"]
        word.save()

        return redirect('/word/view/' + str(pk))

    context = {
        'synonyms': Word.objects.all(),
        'tags': Tag.objects.all(),
        'ipa': word.ipa,
        'wiktionary_link': word.wiktionary_link,
        'descriptions': descriptions,
        'word': word,
        'form': form,
        'word_id': pk,
        'default_variants': default_variants,
        'audio_file': word.audio,
        'user_languages': user_languages,
        'user_moderator': user_moderator,
    }
    return render(request, "word/word_update_form.html", context)


def update_descriptions(request, word):
    for key in request.POST.keys():
        if "desc_short_" in key:
            language_name = key.replace("desc_short_", "")
            desc_short_value = request.POST.get(key, "").strip()
            desc_long_value = request.POST.get("desc_long_" + language_name).strip()
            language_obj = Language.objects.get(name=language_name)

            if not desc_long_value and not desc_short_value:
                old_desc_language = word.desc.filter(language=language_obj)
                word.desc.remove(*old_desc_language)

            if desc_long_value or desc_short_value:
                desc, created = Description.objects.get_or_create(
                    short=desc_short_value,
                    extended=desc_long_value,
                    language=language_obj,
                )
                if created:
                    old_desc_language = word.desc.filter(language=language_obj)
                    word.desc.remove(*old_desc_language)
                word.desc.add(desc)


class WordListView(ListView):
    http_method_names = ['get']
    paginate_by = 10
    template_name = 'word/word_list.html'

    def get_queryset(self):
        words = Word.objects.all()
        words = words.order_by('creation_date')

        return words


class BareWordView(DetailView):
    template_name = 'word/word_detail.html'
    http_method_names = ['get']
    model = Word

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'descriptions': self.object.desc.all(),
            'translations': self.object.translations.all(),
        })
        return context
