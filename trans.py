#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fill <target> for each <source> using known translations (no CDATA).
- Leaves <source> unchanged.
- Writes plain XML-escaped text into <target>.
- Supports a {FEATURE} token that is replaced at runtime with --feature-name.
- Output filename keeps original base but swaps trailing locale (e.g., _en-US) to _<lang>.
- Sets <file ... target-language="<lang>"> in the output.

Usage:
    python trans.py path/to/en-US.xliff
Options:
    --out OUTPUT_DIR       Output directory (default: output)
    --langs zh-CN,es       Comma-separated language codes to process (default: all in translations_by_lang)
    --overwrite            Overwrite non-empty <target> values (default: only fill empty ones)
    --feature-name "Name"  Override the feature name inserted for {FEATURE}
"""

import os
import re
import argparse
import html
from typing import Dict, Optional, Iterable

# ---------------------------------------------------------------------
# 0) Feature name (untranslated) — can be overridden via --feature-name
# ---------------------------------------------------------------------
FEATURE_NAME = "Watermarking"     # default; override with --feature-name
FEATURE_TOKEN = "{FEATURE}"       # token used in DICT KEYS and VALUES

# ---------------------------------------------------------------------
# 1) Translations: English (normalized) -> translated template per language
#    IMPORTANT:
#      - Use {FEATURE} in BOTH the English keys and the translated values.
#      - Keep other placeholders (e.g., {required/}) verbatim. We DO NOT .format().
#      - Keys must match normalized English from the file:
#            "{FEATURE} is easy to use. {required/}"
#            "{FEATURE} meets my needs. {required/}"
# ---------------------------------------------------------------------
translations_by_lang: Dict[str, Dict[str, str]] = {
    "es": { #Spanish
        "Feedback": "Comentario",
        "We'd Love Your Feedback!": "¡Nos encantaría recibir tus comentarios!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} es fácil de usar. {required/}",
        "Strongly Disagree": "Totalmente en desacuerdo",
        "Strongly Agree": "Totalmente de acuerdo",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} satisface mis necesidades. {required/}",
        "Tell us why you gave these ratings.": "Cuéntanos por qué elegiste estas calificaciones.",
        "Remind Me Later": "Recuérdamelo más tarde",
        "Submit": "Enviar",
        "Close": "Cerrar",
        "Thanks for your feedback!": "¡Gracias por tus comentarios!",
        "OK": "Aceptar",
    },

    "fr-FR": { #French (France)
        "Feedback": "Retour",
        "We'd Love Your Feedback!": "Nous aimerions connaître votre avis !",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} est facile à utiliser. {required/}",
        "Strongly Disagree": "Pas du tout d'accord",
        "Strongly Agree": "Tout à fait d'accord",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} répond à mes besoins. {required/}",
        "Tell us why you gave these ratings.": "Dites-nous ce qui a motivé votre évaluation.",
        "Remind Me Later": "Me le rappeler plus tard",
        "Submit": "Soumettre",
        "Close": "Fermer",
        "Thanks for your feedback!": "Merci pour votre retour !",
        "OK": "OK",
    },

    "zh-TW": { #Chinese (Taiwan)
        "Feedback": "回饋",
        "We'd Love Your Feedback!": "我們很想聽聽你的意見回饋！",
        "{FEATURE} is easy to use. {required/}": "{FEATURE}很方便使用。 {required/}",
        "Strongly Disagree": "強烈不同意",
        "Strongly Agree": "非常同意",
        "{FEATURE} meets my needs. {required/}": "{FEATURE}滿足了我的需求。 {required/}",
        "Tell us why you gave these ratings.": "告訴我們你為什麼給這些評分。",
        "Remind Me Later": "稍後提醒我",
        "Submit": "提交",
        "Close": "關閉",
        "Thanks for your feedback!": "感謝你的意見回饋！",
        "OK": "確定",
    },

    "zh-CN": { #Chinese (PRC)
        "Feedback": "反馈",
        "We'd Love Your Feedback!": "我们很想听听你的反馈！",
        "{FEATURE} is easy to use. {required/}": "{FEATURE}简单易用。 {required/}",
        "Strongly Disagree": "强烈不同意",
        "Strongly Agree": "非常同意",
        "{FEATURE} meets my needs. {required/}": "{FEATURE}满足了我的需求。 {required/}",
        "Tell us why you gave these ratings.": "请告知给出这些评分的原因。",
        "Remind Me Later": "稍后提醒我",
        "Submit": "提交",
        "Close": "关闭",
        "Thanks for your feedback!": "谢谢你的反馈！",
        "OK": "确定",
    },

    "ko": { #Korean
        "Feedback": "피드백",
        "We'd Love Your Feedback!": "피드백을 공유해 주시면 감사하겠습니다!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE}는 사용이 쉽습니다. {required/}",
        "Strongly Disagree": "매우 동의 안 함",
        "Strongly Agree": "매우 동의함",
        "{FEATURE} meets my needs. {required/}": "{FEATURE}는 내 필요를 충족합니다. {required/}",
        "Tell us why you gave these ratings.": "이 평점을 부여한 이유를 알려주십시오.",
        "Remind Me Later": "나중에 다시 알림",
        "Submit": "제출",
        "Close": "닫기",
        "Thanks for your feedback!": "피드백을 보내주셔서 감사합니다!",
        "OK": "확인",
    },

    "ru": { #Russian
        "Feedback": "Обратная связь",
        "We'd Love Your Feedback!": "Мы с удовольствием выслушаем ваше мнение!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} проста в использовании. {required/}",
        "Strongly Disagree": "Категорически не согласен",
        "Strongly Agree": "Полностью согласен",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} полностью соответствует моим задачам. {required/}",
        "Tell us why you gave these ratings.": "Расскажите, почему вы поставили такие оценки.",
        "Remind Me Later": "Напомнить позже",
        "Submit": "Отправить",
        "Close": "Закрыть",
        "Thanks for your feedback!": "Благодарим вас за отзыв!",
        "OK": "ОК",
    },

    "pl": { #Polish
        "Feedback": "Opinię",
        "We'd Love Your Feedback!": "Chcielibyśmy poznać Twoją opinię!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} jest łatwy w użyciu. {required/}",
        "Strongly Disagree": "Zdecydowanie się nie zgadzam",
        "Strongly Agree": "Zdecydowanie się zgadzam",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} spełnia moje potrzeby. {required/}",
        "Tell us why you gave these ratings.": "Powiedz nam, dlaczego wystawiłeś(-aś) takie oceny.",
        "Remind Me Later": "Przypomnij mi później",
        "Submit": "Prześlij",
        "Close": "Zamknij",
        "Thanks for your feedback!": "Dzięki za Twoją opinię!",
        "OK": "OK",
    },

    "tr": { #Turkish
        "Feedback": "Geri Bildiriminiz",
        "We'd Love Your Feedback!": "Geri Bildiriminiz Bizim İçin Çok Önemli!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} kullanımı kolaydır. {required/}",
        "Strongly Disagree": "Kesinlikle Katılmıyorum",
        "Strongly Agree": "Kesinlikle Katılıyorum",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} ihtiyaçlarımı karşılıyor. {required/}",
        "Tell us why you gave these ratings.": "Bize bu puanı verme nedeninizi belirtin.",
        "Remind Me Later": "Daha Sonra Hatırlat",
        "Submit": "Gönder",
        "Close": "Kapat",
        "Thanks for your feedback!": "Geri bildiriminiz için teşekkürler!",
        "OK": "Tamam",
    },

    "sv-SE": { #Swedish (Sweden)
        "Feedback": "Feedback",
        "We'd Love Your Feedback!": "Vi skulle verkligen uppskatta din feedback!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} är lätt att använda. {required/}",
        "Strongly Disagree": "Håller absolut inte med",
        "Strongly Agree": "Håller helt med",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} uppfyller mina behov. {required/}",
        "Tell us why you gave these ratings.": "Berätta varför du gav dessa betyg.",
        "Remind Me Later": "Påminn mig senare",
        "Submit": "Skicka",
        "Close": "Stäng",
        "Thanks for your feedback!": "Tack för din feedback!",
        "OK": "OK",
    },

    "ja": { #Japanese
        "Feedback": "フィードバック",
        "We'd Love Your Feedback!": "フィードバックをお待ちしています！",
        "{FEATURE} is easy to use. {required/}": "{FEATURE}は使いやすいです。{required/}",
        "Strongly Disagree": "強く同意しない",
        "Strongly Agree": "強く同意する",
        "{FEATURE} meets my needs. {required/}": "{FEATURE}は私のニーズを満たしている。{required/}",
        "Tell us why you gave these ratings.": "これらの評価を付けた理由を教えてください。",
        "Remind Me Later": "後で通知",
        "Submit": "送信",
        "Close": "閉じる",
        "Thanks for your feedback!": "フィードバックありがとうございます！",
        "OK": "OK",
    },

    "pt-BR": { #Portuguese (Brazil)
        "Feedback": "Feedback",
        "We'd Love Your Feedback!": "Adoraríamos receber seu feedback!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} é fácil de usar. {required/}",
        "Strongly Disagree": "Discordo totalmente",
        "Strongly Agree": "Concordo totalmente",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} atende às minhas necessidades. {required/}",
        "Tell us why you gave these ratings.": "Conte-nos por que você escolheu essas avaliações.",
        "Remind Me Later": "Lembre-me mais tarde",
        "Submit": "Enviar",
        "Close": "Fechar",
        "Thanks for your feedback!": "Agradecemos por seu feedback!",
        "OK": "OK",
    },

    "it": { #Italian
        "Feedback": "Feedback",
        "We'd Love Your Feedback!": "Ci piacerebbe ricevere il tuo feedback!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} è facile da usare. {required/}",
        "Strongly Disagree": "Fortemente in disaccordo",
        "Strongly Agree": "Fortemente d'accordo",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} soddisfa le mie esigenze. {required/}",
        "Tell us why you gave these ratings.": "Dicci perché hai dato queste valutazioni.",
        "Remind Me Later": "Ricordamelo più tardi",
        "Submit": "Invia",
        "Close": "Chiudi",
        "Thanks for your feedback!": "Grazie per il feedback!",
        "OK": "OK",
    },

    "de": { #German
        "Feedback": "Feedback",
        "We'd Love Your Feedback!": "Wir freuen uns über dein Feedback!",
        "{FEATURE} is easy to use. {required/}": "{FEATURE} ist einfach zu verwenden. {required/}",
        "Strongly Disagree": "Stimme überhaupt nicht zu",
        "Strongly Agree": "Stimme voll und ganz zu",
        "{FEATURE} meets my needs. {required/}": "{FEATURE} entspricht meinen Anforderungen. {required/}",
        "Tell us why you gave these ratings.": "Sagen Sie uns, warum Sie diese Bewertungen abgegeben haben.",
        "Remind Me Later": "Später erinnern",
        "Submit": "Senden",
        "Close": "Schließen",
        "Thanks for your feedback!": "Vielen Dank für dein Feedback!",
        "OK": "OK",
    },
}

# ---------------------------------------------------------------------
# 2) Regex to match <source>...</source><target>...</target> pairs
#    Supports with-or-without CDATA for <source> and <target>.
# ---------------------------------------------------------------------
CDATA_SRC  = r"<!\[CDATA\[(?P<src_cdata>.*?)\]\]>"
PLAIN_SRC  = r"(?P<src_plain>.*?)"
SOURCE_ANY = rf"(?:{CDATA_SRC}|{PLAIN_SRC})"

PAIR_PATTERN = re.compile(
    rf"(<source>\s*{SOURCE_ANY}\s*</source>\s*<target>)(?P<tgt>.*?)</target>",
    re.DOTALL
)

CDATA_WRAPPER = re.compile(r"^\s*<!\[CDATA\[(.*)\]\]>\s*$", re.DOTALL)

def strip_cdata(text: str) -> str:
    """If text is a single CDATA section, return inner text; otherwise return as-is."""
    m = CDATA_WRAPPER.match(text)
    return m.group(1) if m else text

def xml_escape(s: str) -> str:
    """Escape special XML characters for text nodes (since we don't use CDATA)."""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))

def normalize_source_from_match(m: re.Match) -> str:
    """Get source text without CDATA/entities and normalize the feature name to {FEATURE}."""
    src_raw = m.group("src_cdata") if m.group("src_cdata") is not None else m.group("src_plain")
    # Unescape XML entities (&apos; etc.) to match plain apostrophes in our keys
    src = html.unescape(strip_cdata(src_raw))
    # Normalize feature name to token for DICT lookup
    if FEATURE_NAME:
        src = src.replace(FEATURE_NAME, FEATURE_TOKEN)
    return src

def denormalize_feature(text: str) -> str:
    """Insert the real FEATURE_NAME where {FEATURE} appears (other braces untouched)."""
    return text.replace(FEATURE_TOKEN, FEATURE_NAME)

def fill_targets_for_lang(file_text: str, lang_map: Dict[str, str], overwrite: bool = False) -> str:
    """
    Replace the <target> content for each <source> pair with mapped translation (no CDATA).
    - Normalize <source> with {FEATURE} for lookup.
    - Insert real FEATURE_NAME back into translation template.
    - If overwrite=False, only fill when target is empty/whitespace.
    - If no translation exists for a <source>, leave the pair unchanged.
    """
    def _replacer(m: re.Match) -> str:
        src_norm = normalize_source_from_match(m)
        tgt_raw = m.group("tgt")
        tgt_stripped = strip_cdata(tgt_raw).strip()

        if not overwrite and tgt_stripped:
            return m.group(0)  # keep existing translation

        translated_template = lang_map.get(src_norm)
        if not translated_template:
            return m.group(0)  # no mapping for this normalized source

        final_text = denormalize_feature(translated_template)
        return m.group(1) + xml_escape(final_text) + "</target>"

    return PAIR_PATTERN.sub(_replacer, file_text)

# ---------------------------------------------------------------------
# 3) Ensure <file ... target-language="..."> matches the output language
#    - If present, replace its value.
#    - If absent, insert target-language="<lang>" into each <file> opening tag.
# ---------------------------------------------------------------------
_FILE_WITH_TLANG = re.compile(r'(<file\b[^>]*\btarget-language=")([^"]*)(")', re.IGNORECASE)
_FILE_TAG_NO_TLANG = re.compile(r'(<file\b(?![^>]*\btarget-language=)[^>]*?)>', re.IGNORECASE)

def set_target_language(file_text: str, lang_code: str) -> str:
    # Replace existing target-language attributes
    replaced, n = _FILE_WITH_TLANG.subn(lambda m: m.group(1) + lang_code + m.group(3), file_text)
    if n > 0:
        return replaced
    # Otherwise, add the attribute to <file ...>
    return _FILE_TAG_NO_TLANG.sub(lambda m: m.group(1) + f' target-language="{lang_code}">', file_text)

# ---------------------------------------------------------------------
# 4) Output filename helper: swap trailing locale to _<lang>
#    Examples:
#      umux-lite_en-US.xliff  -> umux-lite_es.xliff
#      strings.en-GB.xliff    -> strings_es.xliff
#      copy-de_DE.xliff       -> copy_fr-FR.xliff
#      pendo-search.en.xliff  -> pendo-search_zh-CN.xliff
#      guide.xliff            -> guide_ja.xliff
# ---------------------------------------------------------------------
_LOCALE_AT_END = re.compile(r"([_.-])([A-Za-z]{2,3}(?:[._-][A-Za-z]{2})?)$")

def replace_locale_in_filename(src_filename: str, new_lang_code: str) -> str:
    root, ext = os.path.splitext(src_filename)
    m = _LOCALE_AT_END.search(root)
    if m:
        root = root[:m.start()]  # drop separator + locale
    return f"{root}_{new_lang_code}{ext}"

# ---------------------------------------------------------------------
# 5) CLI
# ---------------------------------------------------------------------
def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def selected_langs(all_langs: Iterable[str], arg: Optional[str]):
    if not arg:
        return list(all_langs)
    return [x.strip() for x in arg.split(",") if x.strip()]

def main():
    parser = argparse.ArgumentParser(description="Fill <target> from <source> using known translations (no CDATA, with feature token).")
    parser.add_argument("source_file", help="Path to the English source XLIFF (e.g., umux-lite_en-US.xliff)")
    parser.add_argument("--out", dest="out_dir", default="output", help="Output directory (default: output)")
    parser.add_argument("--langs", dest="langs", default=None, help="Comma-separated language codes to process (default: all present in script)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite non-empty <target> values (default: only fill empty ones)")
    parser.add_argument("--feature-name", dest="feature_name", default=None,
                        help="Feature name to insert (untranslated). Overrides the script's FEATURE_NAME.")
    args = parser.parse_args()

    global FEATURE_NAME
    if args.feature_name is not None:
        FEATURE_NAME = args.feature_name  # override from CLI

    src_path = args.source_file
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source file not found: {src_path}")

    base_text = load_text(src_path)

    # Ensure at least one pair exists
    if not PAIR_PATTERN.search(base_text):
        raise ValueError("No <source>…</source><target>…</target> pairs found in the source file.")

    # Determine languages to process
    langs = selected_langs(translations_by_lang.keys(), args.langs)
    if not langs:
        raise ValueError("No languages selected. Add mappings in translations_by_lang or pass --langs.")

    src_filename = os.path.basename(src_path)

    for lang in langs:
        if lang not in translations_by_lang:
            print(f"⚠️  Skipping {lang}: no translations defined in script.")
            continue

        print(f"→ Processing {lang} … (feature: {FEATURE_NAME})")
        # 1) Fill targets
        merged = fill_targets_for_lang(base_text, translations_by_lang[lang], overwrite=args.overwrite)
        # 2) Ensure <file ... target-language="lang">
        merged = set_target_language(merged, lang)
        # 3) Build output name with locale swapped
        out_filename = replace_locale_in_filename(src_filename, lang)
        out_path = os.path.join(args.out_dir, out_filename)
        save_text(out_path, merged)
        print(f"   ✓ Saved: {out_path}")

    print("Done.")

if __name__ == "__main__":
    main()
