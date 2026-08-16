from dataclasses import (
    dataclass,
    field as dataclasses_field,
)


@dataclass
class SettingsObject:
    """
    The default settings model embed all setting values used in application.
    """
    # Default container label when extension does not match default container list
    default_container_name: str = "Unknow"

    # Non exhaustive list of Media containers with their file extension and name
    medias_containers: dict = dataclasses_field(default_factory=dict)

    # List of unique file extensions for medias automatically build from
    # ``medias_containers`` attribute if not given. It is recommended to let it build
    # automatically.
    medias_extensions: list[str] = dataclasses_field(default_factory=list)

    # Default manifest file name to discover, without format extension
    manifest_name: str = "manifest"

    # Forbidden/reserved keyword from manifest corresponding to computed values from
    # collection (obviously excepted the ones from manifest)
    manifest_forbidden_vars: list = dataclasses_field(default_factory=list)

    # Allowed formats for manifest
    manifest_allowed_formats: tuple[str] = dataclasses_field(default_factory=tuple)

    # File name to use with allowed extensions to search for a cover
    cover_name: str = "cover"

    # Allowed file extensions to search for a cover. The order define the priority when
    # there is multiple cover files in the same directory. The first extension will
    # always have highest priority against other extensions.
    cover_extensions: list[str] = dataclasses_field(default_factory=list)

    # Only these types (from item 'tmdb_type') of manifest are supported
    allowed_manifest_types: tuple[str] = dataclasses_field(default_factory=tuple)

    # List of manifest type that be scrapped
    scrapped_manifest_types: tuple[str] = dataclasses_field(default_factory=tuple)

    # All manifest fields that is known to be filled from tmdb
    supported_tmdb_fields: tuple[str] = dataclasses_field(default_factory=tuple)

    # Default content language requested for detail from TMDB API
    scrapping_language: str = "fr"

    # Default poster size name as expected from TMDB API
    scrapping_cover_size: str = "w780"

    # Default manifest format to output when writing a new manifest
    scrapping_manifest_format: str = "yaml"

    # Default amount of items to process in each chunk
    chunk_size: int = 10

    # Default time in seconds to wait before processing a next chunk
    batch_pause: int = 1

    # Manifest filename to search in a directory
    # DEPRECATED: With new collector the manifest support JSON/YAML and can have
    # different names (for Movie)
    manifest_filename: str = "manifest.yaml"

    def __post_init__(self):
        """
        Fill attributes with default values.
        """
        if not self.medias_containers:
            self.medias_containers = {
                "3gp": "3GPP",
                "asf": "Advanced Systems Format",
                "avi": "AVI",
                "flv": "Flash Video",
                "f4v": "Flash Video",
                "mov": "QuickTime",
                "mp4": "MPEG-4",
                "mkv": "Matroska",
                "mpg": "MPEG",
                "mpeg": "MPEG",
                "mpv": "MPEG",
                "mts": "MPEG Transport Stream",
                "qt": "QuickTime",
                "rm": "RealMedia",
                "ts": "MPEG Transport Stream",
                "vob": "Vob",
                "webm": "WebM",
                "wmv": "Windows Media Video",
            }

        if not self.manifest_allowed_formats:
            self.manifest_allowed_formats = ("json", "yaml")

        if not self.manifest_forbidden_vars:
            # This list has evolved to be used only to ignore some fields from loaded
            # payload.
            self.manifest_forbidden_vars = (
                "path",
                "name",
                "parent",
            )

        if not self.cover_extensions:
            self.cover_extensions = [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
            ]

        if not self.medias_extensions:
            self.medias_extensions = set(self.medias_containers.keys())

        if not self.allowed_manifest_types:
            self.allowed_manifest_types = ("tv", "movie", "collection")

        if not self.scrapped_manifest_types:
            self.scrapped_manifest_types = ("tv", "movie")

        if not self.supported_tmdb_fields:
            self.supported_tmdb_fields = (
                "tmdb_id",
                "tmdb_type",
                "title",
                "overview",
                "status",
                "original_language",
                "casting",
                "crew",
                "genres",
                "first_air_date",
                "number_of_seasons",
                "number_of_episodes",
                "release_date",
            )
