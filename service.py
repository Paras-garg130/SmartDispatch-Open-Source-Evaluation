
from copy import deepcopy
import math


def _valid_id(value):
    return isinstance(value, str) and bool(value.strip())


def _valid_time(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def estimate_eta(order, partner, travel, now=0):

    if not isinstance(order, dict) or not isinstance(partner, dict):
        return {
            'partner_id': None,
            'eta_minutes': None,
            'eligible': False,
            'reason': 'malformed order or partner'
        }

    if not isinstance(travel, dict):
        return {
            'partner_id': partner.get('partner_id'),
            'eta_minutes': None,
            'eligible': False,
            'reason': 'invalid travel data'
        }

    required_ids = [
        order.get('order_id'),
        order.get('restaurant_id'),
        order.get('destination_zone'),
        partner.get('partner_id'),
        partner.get('zone')
    ]

    if not all(_valid_id(value) for value in required_ids):
        return {
            'partner_id': partner.get('partner_id'),
            'eta_minutes': None,
            'eligible': False,
            'reason': 'invalid identifiers'
        }

    workload = partner.get('workload_minutes', 0)
    prep = order.get('prep_minutes')

    if not all(_valid_time(value) for value in (now, workload, prep)):
        return {
            'partner_id': partner.get('partner_id'),
            'eta_minutes': None,
            'eligible': False,
            'reason': 'invalid time values'
        }

    leg1_key = (partner['zone'], order['restaurant_id'])
    leg2_key = (order['restaurant_id'], order['destination_zone'])

    if leg1_key not in travel or leg2_key not in travel:
        return {
            'partner_id': partner['partner_id'],
            'eta_minutes': None,
            'eligible': False,
            'reason': 'missing travel data'
        }

    leg1 = travel[leg1_key]
    leg2 = travel[leg2_key]

    if not _valid_time(leg1) or not _valid_time(leg2):
        return {
            'partner_id': partner['partner_id'],
            'eta_minutes': None,
            'eligible': False,
            'reason': 'invalid travel time'
        }

    pickup = now + leg1 + workload

    eta = pickup + prep + leg2

    return {
        'partner_id': partner['partner_id'],
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
        'reason': 'eligible'
    }


def assign_order(order, partners, travel, now=0):

    order_id = order.get('order_id') if isinstance(order, dict) else None

    def unassigned(reason):
        return {
            'order_id': order_id,
            'partner_id': None,
            'pickup_minutes': None,
            'eta_minutes': None,
            'reason': reason
        }

    if not isinstance(order, dict):
        return unassigned('malformed order')

    if not isinstance(partners, (list, tuple)):
        return unassigned('invalid partners list')

    if not isinstance(travel, dict):
        return unassigned('invalid travel data')

    if not _valid_id(order.get('order_id')):
        return unassigned('invalid order ID')

    if not _valid_id(order.get('restaurant_id')):
        return unassigned('invalid restaurant ID')

    if not _valid_id(order.get('destination_zone')):
        return unassigned('invalid destination zone')

    if not _valid_time(order.get('prep_minutes')):
        return unassigned('invalid preparation time')

    if not _valid_time(now):
        return unassigned('invalid current time')

    options = []
    rejection_reasons = set()
    partner_ids = set()

    for partner in partners:

        if not isinstance(partner, dict):
            rejection_reasons.add('malformed partner')
            continue

        partner_id = partner.get('partner_id')

        if not _valid_id(partner_id):
            rejection_reasons.add('invalid partner ID')
            continue

        if partner_id in partner_ids:
            rejection_reasons.add('duplicate partner ID')
            continue

        partner_ids.add(partner_id)

        if partner.get('active') is not True:
            rejection_reasons.add('inactive partner')
            continue

        capacity = partner.get('capacity')
        active_orders = partner.get('active_order_ids')

        if (
            not isinstance(capacity, int)
            or isinstance(capacity, bool)
            or capacity < 0
        ):
            rejection_reasons.add('invalid partner capacity')
            continue

        if not isinstance(active_orders, list):
            rejection_reasons.add('invalid active order list')
            continue

        if len(active_orders) >= capacity:
            rejection_reasons.add('partner capacity reached')
            continue

        estimate = estimate_eta(order, partner, travel, now)

        if estimate['eligible']:
            options.append(estimate)
        else:
            rejection_reasons.add(estimate['reason'])

    if not options:
        return unassigned(
            'no eligible partner: ' + '; '.join(sorted(rejection_reasons))
            if rejection_reasons else 'no eligible partner'
        )

    chosen = min(
        options,
        key=lambda item: (item['eta_minutes'], item['partner_id'])
    )

    return {
        'order_id': order_id,
        'partner_id': chosen['partner_id'],
        'pickup_minutes': chosen['pickup_minutes'],
        'eta_minutes': chosen['eta_minutes'],
        'reason': 'assigned'
    }


def process_cancellation(partner, order_id, event_id):
    return deepcopy(partner)
