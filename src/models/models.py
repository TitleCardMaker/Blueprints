# pyright: reportInvalidTypeForm=false
from typing import Literal

from pydantic import (
    BaseModel, HttpUrl, PositiveFloat, conlist, constr, root_validator
)

SeasonTitleRange = constr(regex=r'^(\d+-\d+)|^(\d+)|^(s\d+e\d+-s\d+e\d+)$')
TitleCase = Literal['blank', 'lower', 'source', 'title', 'upper']

class Condition(BaseModel):
    argument: constr(min_length=1)
    operation: constr(min_length=1)
    reference: str | None = None

class Translation(BaseModel):
    language_code: constr(min_length=1)
    data_key: constr(regex=r'^[a-zA-Z]+[^ -]*$', min_length=1)

class BlueprintBase(BaseModel):
    ...

class SeriesBase(BlueprintBase):
    font_id: int | None = None
    card_type: constr(min_length=1) | None = None
    hide_season_text: bool | None = None
    hide_episode_text: bool | None = None
    episode_text_format: str | None = None
    translations: list[Translation] | None = None
    season_titles: dict[SeasonTitleRange, str] | None = None
    extras: dict[constr(min_length=1), str] | None = None
    skip_localized_images: bool | None = None

class BlueprintSeries(SeriesBase):
    template_ids: conlist(int, unique_items=True) = []
    match_titles: bool | None = None
    font_color: constr(min_length=1) | None = None
    font_title_case: TitleCase | None = None
    font_size: PositiveFloat | None = None
    font_kerning: float | None = None
    font_stroke_width: float | None = None
    font_interline_spacing: int | None = None
    font_vertical_shift: int | None = None
    source_files: conlist(constr(min_length=3), unique_items=True) = []
    
class BlueprintEpisode(BlueprintSeries):
    title: str | None = None
    match_title: bool | None = None
    season_text: str | None = None
    episode_text: str | None = None

class BlueprintFont(BlueprintBase):
    name: constr(min_length=1)
    color: constr(min_length=1) | None = None
    delete_missing: bool = None
    file: constr(min_length=3) | None = None
    file_download_url: HttpUrl | None = None
    kerning: float = None
    interline_spacing: int = None
    replacements_in: conlist(constr(min_length=1), unique_items=True) = None
    replacements_out: list[str] = None
    size: PositiveFloat = None
    stroke_width: float = None
    title_case: TitleCase | None = None
    vertical_shift: int = None

    @root_validator(skip_on_failure=True)
    def validate_both_not_provided(cls, values: dict) -> dict:
        if (values.get('file', None) is not None
            and values.get('file_download_url', None) is not None):
            raise ValueError('Cannot provide both a Font file and download URL')

        return values

class BlueprintTemplate(SeriesBase):
    name: constr(min_length=1)
    filters: list[Condition] = []

class Blueprint(BaseModel):
    series: BlueprintSeries
    episodes: dict[constr(regex=r's\d+e\d+'), BlueprintEpisode] = {}
    templates: list[BlueprintTemplate] = []
    fonts: list[BlueprintFont] = []
    creator: constr(min_length=1, max_length=40)
    previews: conlist(constr(min_length=3), min_items=1, max_items=5, unique_items=True)
    description: conlist(constr(min_length=1, max_length=250), min_items=1, max_items=5)

    @root_validator(skip_on_failure=True)
    def validate_template_specifications(cls, values: dict) -> dict:
        # Get all unique Template IDs
        template_ids = set(values['series'].template_ids)
        for episode in values['episodes'].values():
            if hasattr(episode, 'template_ids') and episode.template_ids:
                template_ids.update(id_ for id_ in episode.template_ids)

        # Verify Template specification
        templates_used = max(template_ids)+1 if template_ids else 0
        assert not (templates_used > len(values['templates'])), f'Not all Templates are defined in {values}'
        assert not (templates_used < len(values['templates'])), f'Not all Templates are utilized in {values}'

        return values
    
    @root_validator(skip_on_failure=True)
    def validate_font_specifications(cls, values: dict) -> dict:
        # Get all unique Font IDs
        font_ids = set() if values['series'].font_id is None else set([values['series'].font_id])
        for episode in values['episodes'].values():
            if hasattr(episode, 'font_id') and episode.font_id is not None:
                font_ids.add(episode.font_id)
        for template in values['templates']:
            if hasattr(template, 'font_id') and template.font_id is not None:
                font_ids.add(template.font_id)

        # Verify Font specification
        fonts_used = max(font_ids)+1 if font_ids else 0
        assert not (fonts_used > len(values['fonts'])), f'Not all Fonts are defined in {values}'
        assert not (fonts_used < len(values['fonts'])), f'Not all Fonts are utilized in {values}'

        return values

class BlueprintSet(BaseModel):
    id: int
    name: constr(min_length=3)
    blueprint_ids: conlist(int, min_items=2, unique_items=True)
