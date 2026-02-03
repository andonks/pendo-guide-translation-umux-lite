Each UMUX-lite guide is almost identical to all other UMUX-lite guides; only the product/feature name changes. 
This program contains a dictionary of translated pairs for each text block for each language, and a configurable {FEATURE} variable to define the feature name. 
You input the English-language XLIFF file from Pendo, and it outputs one XLIFF file for each supported language that can be imported back into Pendo. 

Use **trans-my-docs.py** when the feature name IS translated in our UI. The translated name must be entered in the dictionary for each target language.  
Use **trans.py** when the feature name IS NOT translated. The English name will be used in all output files.  

```
Fill <target> for each <source> using known translations.
- Leaves <source> unchanged.
- Writes plain XML-escaped text into <target>.
- Supports a {FEATURE} token that is replaced at runtime with --feature-name.
- Output filename keeps original base but swaps trailing locale (e.g., _en-US) to _<lang>.

Usage:
    python trans.py path/to/en-US.xliff
Options:
    --out OUTPUT_DIR       Output directory (default: output)
    --langs zh-CN,es       Comma-separated language codes to process (default: all in translations_by_lang)
    --overwrite            Overwrite non-empty <target> values (default: only fill empty ones)
    --feature-name "Name"  Override the feature name inserted for {FEATURE}
```

Supported Language/ISO codes:
- Spanish (es)
- French (fr-FR)
- Chinese(Taiwan) (zh-TW)
- Chinese(PRC) (zh-CN)
- Korean (ko)
- Russian (ru)
- Polish (pl)
- Turkish (tr)
- Swedish (sv-SE)
- Japanese (ja)
- Portuguese(Brazilian) (pt-BR)
- Italian (it)
- German (de)

