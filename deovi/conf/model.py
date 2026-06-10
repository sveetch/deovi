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

    # Manifest filename to search in a directory
    manifest_filename: str = "manifest.yaml"

    # Forbidden/reserved keyword from manifest corresponding to computed values from
    # collection (obviously excepted the ones from manifest)
    manifest_forbidden_vars: dict = dataclasses_field(default_factory=dict)

    # File name to use with allowed extensions to search for a cover
    cover_name: str = "cover"

    # Allowed file extensions to search for a cover. The order define the priority when
    # there is multiple cover files in the same directory. The first extension will
    # always have highest priority against other extensions.
    cover_extensions: list[str] = dataclasses_field(default_factory=list)

    def __post_init__(self):
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

        if not self.manifest_forbidden_vars:
            self.manifest_forbidden_vars = {
                "path",
                "name",
                "absolute_dir",
                "relative_dir",
                "size",
                "mtime",
                "checksum",
                "children_files",
                "cover",
            }

        if not self.cover_extensions:
            self.cover_extensions = [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
            ]

        if not self.medias_extensions:
            self.medias_extensions = set(self.medias_containers.keys())
