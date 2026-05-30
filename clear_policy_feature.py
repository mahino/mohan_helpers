#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage -
1. Enter Calm container on PC - "docker exec -it nucalm bash"
2. Activate venv - "activate"
3. Get this script - "wget
http://filer.dev.eng.nutanix.com:8080/Users/calm-policy-engine/scripts/clear_policy_feature.py" or
from some other place.
4. Run - "python clear_policy_feature.py"

Run this script to clear db entry of policy feature.
You will have to manually delete old policy vm if that exists.
"""


from calm.common.flags import gflags
import logging
import traceback
from calm.common.config import init_config, get_config
from calm.lib.model.feature import Feature as FeatureModel
from calm.lib.constants import FEATURE
from calm.pkg.common.scramble import init_scramble

log = logging.getLogger(__name__)
FLAGS = gflags.FLAGS
FLAGS({})
cfg = init_config()

keyfile = cfg.get('security', 'keyfile')
init_scramble(keyfile)

from calm.lib.model.store.base import CalmModelBase as ModelBase  # noqa
from calm.lib.model.store.db_session import create_session, set_session_type, flush_session, set_second_session_type  # noqa
from calm.lib.model.store.idf.db import create_db_connection  # noqa


def get_all_subclasses(cls):
    """Get all subclasses."""
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def init_contexts():
    """Init contexts."""
    cfg = get_config()
    set_session_type('green', cfg.get('store', 'flush_parallelisation_factor'), cfg.get('store', 'bulk_size'))
    set_second_session_type('postgres', cfg.get('store', 'pg_enabled'), cfg.get('store', 'pg_ip'))
    create_db_connection(register_entities=False)
    create_session()


def clean_policy_feature():
    """Clean policy feature entry"""
    feature = FeatureModel.query(type=FEATURE.TYPE.POLICY, deleted=False)[0]
    print("Current Feature status = {}".format(feature.to_status({})))
    print("Current Feature config = {}".format(feature.feature_status.config))

    feature.feature_status.config = None
    feature.feature_status.is_enabled = False
    feature.feature_status.is_ignored = False
    feature.save()
    try:
        flush_session()
    except Exception:
        log.error("Got the traceback\n{}".format(traceback.format_exc()))
        print("Failed.")
        exit(1)
    else:
        print("Success.")


def print_policy_feature():
    """Clean policy feature entry"""
    feature = FeatureModel.query(type=FEATURE.TYPE.POLICY, deleted=False)[0]
    print("After reset - Feature status = {}".format(feature.to_status({})))
    print("After reset - Feature config = {}".format(feature.feature_status.config))


def main():
    """Clean mark delete main function."""
    print("Cleaning all mark deleted objects..")
    init_contexts()
    clean_policy_feature()
    print_policy_feature()

if __name__ == '__main__':
    main()