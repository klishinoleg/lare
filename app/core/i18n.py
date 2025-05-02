from fastapi18n.wrappers import TranslationWrapper
from core.config import settings

TranslationWrapper.init(
    locales_dir=settings.get_locales_dir(),
    languages=settings.get_languages(),
    language=settings.language_code
)

_ = TranslationWrapper.get_instance().gettext
activate = TranslationWrapper.get_instance().set_locale
