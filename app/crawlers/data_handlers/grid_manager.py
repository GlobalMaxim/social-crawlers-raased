import json
import random
import requests
from pydantic import HttpUrl
from pydantic.error_wrappers import ValidationError
from requests.exceptions import Timeout
from app.core.config import settings
from app.schemas.selenium_grid_status import SeleniumGridStatus
from app.exceptions.grid import SeleniumGridURLNotFound

_REQUEST_TIMEOUTS = (5, 5)


def _calculate_grid_load(status: SeleniumGridStatus, queue_size: int) -> int:
    '''
    Calculate load of grid nodes
    Algorithm: 
    - get total of nodes and slots in them (e.g. 2 x nodes 12 slots each = 24 slots total)
    - get number of free slots in each node
    - calculate load percentage for slots and queue (e.g. 6 / 24 * 100 = 25)
    - return sum of slots and queue load percentage (max 200)
    TODO 
    - more accurate queue to slots load ratio algorithm
    - advanced error handling and validation for response from /status
    - return grids only with requested browser (browserName)
    - better logging
    - async http requests (non-blocking)
    - use GraphQL to query status (https://www.selenium.dev/documentation/grid/advanced_features/graphql_support/)
    '''
    slots_total = 0
    slots_active = 0
    for node in status.value.nodes:
        slots_total += len(node.slots)
        for slot in node.slots:
            if slot.session is not None:
                slots_active += 1
    load_slots = round((slots_active / slots_total) * 100)
    load_queue = round((queue_size / slots_total) * 100)
    return load_slots + load_queue


def _get_grids_status(grids: list[HttpUrl]) -> list[dict]:
    '''
    Get status and queue length from Selenium Grid instance
    '''
    grids_with_status: list[dict] = []
    grid: HttpUrl
    for grid in grids:
        grid_base_url = f'{grid.scheme}://{grid.host}:{grid.port}'
        grid_status_url = f'{grid_base_url}/status'
        grid_queue_url = f'{grid_base_url}/se/grid/newsessionqueue/queue'

        try:
            response = requests.get(grid_status_url, timeout=_REQUEST_TIMEOUTS)
            if response:
                grid_status_dict = json.loads(response.content)
                grid_status_schema = SeleniumGridStatus.parse_obj(grid_status_dict)
            else:
                print(f'HTTP ERROR {response.status_code}: {grid_status_url}')
                continue
            response = requests.get(grid_queue_url, timeout=_REQUEST_TIMEOUTS)
            if response:
                grid_queue_dict = json.loads(response.content)
                grid_queue_size = len(grid_queue_dict['value'])
            else:
                print(f'HTTP ERROR {response.status_code}: {grid_queue_url}')
                continue
        except Timeout as t:
            print(f'The request to {t.request.url} timed out')
            continue
        except json.JSONDecodeError:
            print(f'Error decoding JSON from {grid_status_url}')
            continue
        except ValidationError:
            print(f'Error parsing dict to schema')
            continue
        if grid_status_schema.value.ready:
            grid_load_percent = _calculate_grid_load(grid_status_schema, grid_queue_size)
            grids_with_status.append({
                'url': grid,
                'load': grid_load_percent
            })
    return grids_with_status


def get_active_grid_host(browserName: str) -> str:
    '''
    Get least busy Selenium Grid instance
    - shuffle grid urls in list
    - get status for each grid
    - get the grid with minimum load percentage
    - return grid host (e.g. 123.234.44.55, grid.example.com)
    '''
    grids = settings.REMOTE_SELENIUM_GRIDS
    random.shuffle(grids)
    grids_with_status = _get_grids_status(grids)
    if len(grids_with_status) == 0:
        raise SeleniumGridURLNotFound
    idle_grid = min(grids_with_status, key=lambda x: x['load'])
    grid_url: HttpUrl = idle_grid['url']
    return grid_url.host

def get_active_grid(browserName: str) -> str:
    '''
    Get least busy Selenium Grid instance
    - shuffle grid urls in list
    - get status for each grid
    - get the grid with minimum load percentage
    - return grid HttpUrl
    '''
    grids = settings.REMOTE_SELENIUM_GRIDS[4:]
    random.shuffle(grids)
    grids_with_status = _get_grids_status(grids)
    if len(grids_with_status) == 0:
        raise SeleniumGridURLNotFound
    idle_grid = min(grids_with_status, key=lambda x: x['load'])
    grid_url: HttpUrl = idle_grid['url']
    print('Current grid url: ', str(grid_url))
    return str(grid_url)