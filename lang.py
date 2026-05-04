import json
import os


class I18n:
    _instance = None
    _current_lang = None
    _translations = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._load_config()

    def _load_config(self):
        config_path = "data/config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self._current_lang = config.get("lang", "zh-CN")
            except Exception:
                self._current_lang = "zh-CN"
        else:
            self._current_lang = "zh-CN"
        self._load_translations()

    def _load_translations(self):
        self._translations = {}
        lang_dir = "languages"
        if os.path.exists(lang_dir):
            for filename in os.listdir(lang_dir):
                if filename.endswith(".json"):
                    lang_id = filename[:-5]
                    filepath = os.path.join(lang_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            self._translations[lang_id] = json.load(f)
                    except Exception:
                        pass

    def get(self, key, default=None):
        if self._current_lang not in self._translations:
            return default or key
        
        value = self._translations[self._current_lang]
        keys = key.split('.')
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default or key
        
        return value

    def get_from_lang(self, lang_id, key, default=None):
        if lang_id not in self._translations:
            return default or key
        
        value = self._translations[lang_id]
        keys = key.split('.')
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default or key
        
        return value

    def set_lang(self, lang_id):
        if lang_id in self._translations:
            self._current_lang = lang_id
            config_path = "data/config.json"
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump({"lang": lang_id}, f, ensure_ascii=False)
            except Exception:
                pass

    def current_lang(self):
        return self._current_lang

    def available_langs(self):
        return list(self._translations.keys())


def _(key, default=None):
    return I18n.get_instance().get(key, default)
