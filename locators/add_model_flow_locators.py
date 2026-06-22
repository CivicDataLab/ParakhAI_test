"""Selectors for the Add Model cross-platform flow (ParakhAI → CivicDataSpace)."""


class AddModelFlowLocators:
    ADD_NEW_MODEL_BUTTON = "button:has-text('Add A New Model'), button:has-text('Add New AI Model')"
    REDIRECT_DIALOG = "[role='dialog']:has-text('CivicDataSpace'), [role='alertdialog']"
    REDIRECT_CONFIRM_BTN = (
        "[role='dialog'] button:has-text('Go'), "
        "[role='dialog'] button:has-text('CivicDataSpace'), "
        "[role='dialog'] button:has-text('Proceed')"
    )
    REDIRECT_CANCEL_BTN = "[role='dialog'] button:has-text('Cancel')"

    CDS_ADD_MODEL_BTN = "button:has-text('Add New AI Model'), button:has-text('Add AI Model')"
    CDS_STEP1_TITLE_INPUT = (
        "input[name='title'], input[placeholder*='title'], input[placeholder*='model name']"
    )
    CDS_NEXT_BTN = "button:has-text('Next'), button:has-text('Save & Continue')"
    CDS_AUTOSAVE_INDICATOR = "text=All Changes Saved, text=Saved"
    CDS_STEP_INDICATOR = "[aria-label*='step'], .step-indicator, [data-step]"
    CDS_PUBLISH_BTN = "button:has-text('Publish')"
    CDS_ADD_ACCESS_METHOD_BTN = "button:has-text('Add New Access Method')"
    CDS_API_KEY_INPUT = (
        "input[type='password'][name*='key'], input[name*='apiKey'], input[placeholder*='API']"
    )
    CDS_QUILL_BULLET_BTN = ".ql-bullet, .ql-list[value='bullet']"
