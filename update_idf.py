

# Refer this sheet for queries - https://docs.google.com/spreadsheets/d/1OSYe7hn_hQpzuuwZ98pP4w6LpbIu2b99dpd4nUtk3eI/edit#gid=705111080
# usage: python3 inject_idf_data.py -app_count=2 (default value app_count = 1, #no.of applications data to be relfect in different tables with respective ratio.)

from calm.common.flags import gflags
import sys
import argparse
import logging
import traceback
from calm.common.config import init_config, get_config
from calm.lib.model.feature import Feature as FeatureModel
from calm.lib.constants import FEATURE

log = logging.getLogger(__name__)
FLAGS = gflags.FLAGS
FLAGS({})
cfg = init_config()

from calm.lib.model.store.base import CalmModelBase as ModelBase  # noqa
from calm.lib.model.store.db_session import create_session, set_session_type, flush_session  # noqa
from calm.lib.model.store.idf.db import create_db_connection  # noqa
from calm.lib import model

entities = [
  ("task", model.Task, 375),
  ("runbook", model.Runbook, 150),
  ("action", model.Action, 140),
  ("variable",model.LocalVariable, 150),
  ("runlog", model.RunLog, 10),
  ("lifecycle", model.Lifecycle, 5)
]

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
    create_db_connection(register_entities=False)
    create_session()

def inject_data(app_count):
    class_name = model.Action
    for i in range(2671,3544):
        print(f"Updating from [{i}*100] to [{(i+1)*100}]")
        rl = class_name.query(length=100, offset=i * 100)
        for entry in rl:
            entry['annotations'] = {}
            entry['attrs'] = {}
            entry['entity_task_edge_list'] = []
            entry['messages'] = []
            entry['cloned_from_reference'] = None
            entry['prerun_runbook_reference'] = None
            entry['postrun_runbook_reference'] = None
            entry['tunnels_used_references'] = []
            entry['resource_type_reference_list'] = []
            entry.save()
            flush_session()
        print(f"Updated from [{i}] to [{(i+1)*100}]")

def main():
    """Seed Data"""
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("-app_count", type=int, default=1, help="The count of the app (default: 1)")
    args = parser.parse_args()
    print("Init contexts")
    init_contexts()
    print("Init contexts")
    inject_data(args.app_count + 1)

if __name__ == '__main__':
    main()