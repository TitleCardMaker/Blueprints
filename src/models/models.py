# pyright: reportInvalidTypeForm=false
from typing import Literal, Optional

from pydantic import (
    BaseModel, HttpUrl, PositiveFloat, conlist, constr, root_validator
)

SeasonTitleRange = constr(regex=r'^(\d+-\d+)|^(\d+)|^(s\d+e\d+-s\d+e\d+)$')
TitleCase = Literal['blank', 'lower', 'source', 'title', 'upper']

class Condition(BaseModel):
    argument: constr(min_length=1)
    operation: constr(min_length=1)
    reference: Optional[str] = None

class Translation(BaseModel):
    language_code: constr(min_length=1)
    data_key: constr(regex=r'^[a-zA-Z]+[^ -]*$', min_length=1)

class BlueprintBase(BaseModel):
    ...

class SeriesBase(BlueprintBase):
    font_id: Optional[int] = None
    card_type: Optional[constr(min_length=1)] = None
    hide_season_text: Optional[bool] = None
    hide_episode_text: Optional[bool] = None
    episode_text_format: Optional[str] = None
    translations: Optional[list[Translation]] = None
    season_title_ranges: list[SeasonTitleRange] = []
    season_title_values: list[str] = []
    extra_keys: conlist(constr(min_length=1), unique_items=True) = []
    extra_values: list[str] = []
    skip_localized_images: Optional[bool] = None

    @root_validator(skip_on_failure=True)
    def validate_paired_lists(cls, values: dict) -> dict:
        # Season title ranges
        st_ranges = values.get('season_title_ranges', [])
        st_values = values.get('season_title_values', [])
        assert len(st_ranges) == len(st_values), 'Season title ranges and values must be equal length'
        # Extras
        ex_ranges = values.get('extra_keys', [])
        ex_values = values.get('extra_values', [])
        assert len(ex_ranges) == len(ex_values), 'Extra keys and values must be equal length'

        return values

class BlueprintSeries(SeriesBase):
    template_ids: conlist(int, unique_items=True) = []
    match_titles: Optional[bool] = None
    font_color: Optional[constr(min_length=1)] = None
    font_title_case: Optional[TitleCase] = None
    font_size: Optional[PositiveFloat] = None
    font_kerning: Optional[float] = None
    font_stroke_width: Optional[float] = None
    font_interline_spacing: Optional[int] = None
    font_vertical_shift: Optional[int] = None
    source_files: conlist(constr(min_length=3), unique_items=True) = []
    
class BlueprintEpisode(BlueprintSeries):
    title: Optional[str] = None
    match_title: Optional[bool] = None
    season_text: Optional[str] = None
    episode_text: Optional[str] = None

class BlueprintFont(BlueprintBase):
    name: constr(min_length=1)
    color: Optional[constr(min_length=1)] = None
    delete_missing: bool = None
    file: Optional[constr(min_length=3)] = None
    file_download_url: Optional[HttpUrl] = None
    kerning: float = None
    interline_spacing: int = None
    replacements_in: conlist(constr(min_length=1), unique_items=True) = None
    replacements_out: list[str] = None
    size: PositiveFloat = None
    stroke_width: float = None
    title_case: Optional[TitleCase] = None
    vertical_shift: int = None

    @root_validator(skip_on_failure=True)
    def validate_both_not_provided(cls, values: dict) -> dict:
        if (values.get('file', None) is not None
            and values.get('file_download_url', None) is not None):
            raise ValueError(f'Cannot provide both a Font file and download URL')

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
