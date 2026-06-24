from bson.objectid import ObjectId
from rest_framework.response import Response
from rest_framework import status

from .enums import Platform, MatchMode, ContentType

MAX_KEYWORD_LENGTH = 255
MAX_FILTER_COUNT = 50
MAX_FILTER_ITEM_LENGTH = 200

VALID_PLATFORMS = {p.value for p in Platform}
SPECIFIC_PLATFORMS = {p.value for p in Platform if p != Platform.ALL}


def _bad_request(message: str) -> Response:
    return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


def validate_keyword_id(keyword_id: str) -> Response | None:
    if not ObjectId.is_valid(keyword_id) or str(ObjectId(keyword_id)) != keyword_id:
        return _bad_request('Invalid keyword id')
    return None


def parse_keyword_text(raw) -> tuple[str | None, Response | None]:
    if raw is None:
        return None, _bad_request('keyword is required')
    if not isinstance(raw, str):
        return None, _bad_request('keyword must be a string')
    keyword = raw.strip()
    if not keyword:
        return None, _bad_request('keyword is required')
    if len(keyword) > MAX_KEYWORD_LENGTH:
        return None, _bad_request(f'keyword must be at most {MAX_KEYWORD_LENGTH} characters')
    return keyword, None


def parse_platform(raw, *, url_platform: str | None = None) -> tuple[str | None, Response | None]:
    if url_platform is not None:
        if url_platform not in SPECIFIC_PLATFORMS:
            return None, _bad_request(f'platform must be one of: {", ".join(sorted(SPECIFIC_PLATFORMS))}')
        if raw is not None and raw != url_platform:
            return None, _bad_request('platform in request body must match the URL platform')
        return url_platform, None

    platform = raw if raw is not None else Platform.REDDIT.value
    if not isinstance(platform, str):
        return None, _bad_request('platform must be a string')
    if platform not in VALID_PLATFORMS:
        return None, _bad_request(f'platform must be one of: {", ".join(sorted(VALID_PLATFORMS))}')
    return platform, None


def parse_string_list(raw, field_name: str) -> tuple[list[str] | None, Response | None]:
    if raw is None:
        return [], None
    if isinstance(raw, str):
        raw = [part.strip() for part in raw.split(',') if part.strip()]
    if not isinstance(raw, list):
        return None, _bad_request(f'{field_name} must be a list of strings')

    values: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            return None, _bad_request(f'{field_name} must be a list of strings')
        value = item.strip()
        if not value:
            continue
        if len(value) > MAX_FILTER_ITEM_LENGTH:
            return None, _bad_request(
                f'each {field_name} entry must be at most {MAX_FILTER_ITEM_LENGTH} characters'
            )
        values.append(value)

    if len(values) > MAX_FILTER_COUNT:
        return None, _bad_request(f'{field_name} supports at most {MAX_FILTER_COUNT} entries')
    return values, None


def parse_platform_filters(raw) -> tuple[list[str] | None, Response | None]:
    return parse_string_list(raw, 'platformSpecificFilters')


def parse_case_sensitive(raw, *, default: bool = False) -> tuple[bool | None, Response | None]:
    if raw is None:
        return default, None
    if not isinstance(raw, bool):
        return None, _bad_request('caseSensitive must be a boolean')
    return raw, None


def parse_match_mode(raw, *, default: str | None = None) -> tuple[str | None, Response | None]:
    from .enums import MatchMode
    if raw is None:
        return default or MatchMode.CONTAINS.value, None
    if not isinstance(raw, str):
        return None, _bad_request('matchMode must be a string')
    valid_modes = {mode.value for mode in MatchMode}
    if raw not in valid_modes:
        return None, _bad_request(f'matchMode must be one of: {", ".join(sorted(valid_modes))}')
    return raw, None


def parse_content_types(raw, *, platform: str | None = None) -> tuple[list[str] | None, Response | None]:
    from .enums import ContentType, DEFAULT_CONTENT_TYPES
    if raw is None:
        default_platform = platform or Platform.REDDIT.value
        return DEFAULT_CONTENT_TYPES.get(default_platform, [
            ContentType.TITLES.value,
            ContentType.BODY.value,
            ContentType.COMMENTS.value,
        ]), None
    if not isinstance(raw, list):
        return None, _bad_request('contentTypes must be a list of strings')

    valid_types = {ct.value for ct in ContentType}
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            return None, _bad_request('contentTypes must be a list of strings')
        if item not in valid_types:
            return None, _bad_request(f'contentTypes must be one of: {", ".join(sorted(valid_types))}')
        if item not in values:
            values.append(item)

    if not values:
        return None, _bad_request('contentTypes must include at least one value')
    return values, None


def parse_enabled(raw, *, default: bool = True) -> tuple[bool | None, Response | None]:
    if raw is None:
        return default, None
    if not isinstance(raw, bool):
        return None, _bad_request('enabled must be a boolean')
    return raw, None
