from deovi.collector import MANIFEST_FILENAME, MANIFEST_FORBIDDEN_VARS, Collector


def test_collector_get_directory_manifest_nofile(manifests_sample):
    """
    Collector should silently fail if there is no manifest.
    """
    collector = Collector(None)
    manifest = collector.get_directory_manifest(manifests_sample)

    assert manifest == {}


def test_collector_get_directory_manifest_invalid(caplog, warning_logger,
                                                  manifests_sample):
    """
    Collector should not break process if found manifest file is invalid and emits
    a warning log.
    """
    collector = Collector(None)
    sample_dir = manifests_sample / "invalid"
    manifest_path = sample_dir / MANIFEST_FILENAME
    manifest = collector.get_directory_manifest(sample_dir)

    assert manifest == {}

    assert caplog.record_tuples == [
        (
            "deovi",
            30,
            "No YAML object could be decoded for manifest: {}".format(manifest_path)
        ),
    ]


def test_collector_get_directory_manifest_forbidden(caplog, warning_logger,
                                                    manifests_sample):
    """
    Collector should not break process if manifest contains forbidden keywords but it
    results to a warning and ignored manifest.
    """
    collector = Collector(None)
    sample_dir = manifests_sample / "forbidden"
    manifest_path = sample_dir / MANIFEST_FILENAME
    manifest = collector.get_directory_manifest(sample_dir)

    assert manifest == {}

    # Forbidden keywords
    names = ", ".join([
        item
        for item in MANIFEST_FORBIDDEN_VARS
        if item not in ["checksum"]
    ])

    msg = "Ignored manifest because it has forbidden keywords '{}': {}"
    assert caplog.record_tuples == [
        (
            "deovi",
            30,
            msg.format(names, manifest_path)
        ),
    ]


def test_collector_get_directory_manifest_basic(manifests_sample):
    """
    Collector should find manifest if any and correctly load it.
    """
    collector = Collector(None)
    manifest = collector.get_directory_manifest(manifests_sample / "basic")

    assert manifest == {
        "foo": "bar",
        "ping": {
            "pong": True,
            "pang": 4
        },
        "nope": None,
        "plop": [
            True,
            False,
            True,
            False,
            "plip"
        ],
        "pika": [
            "chu",
            {
                "pika": "map"
            }
        ]
    }
