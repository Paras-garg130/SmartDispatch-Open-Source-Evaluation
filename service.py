
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

    if not _valid_id(order.get('order_id')):
        reason = 'invalid order ID'
    elif not _valid_id(order.get('restaurant_id')):
        reason = 'invalid restaurant ID'
    elif not _valid_id(order.get('destination_zone')):
        reason = 'invalid destination zone'
    elif not _valid_id(partner.get('partner_id')):
        reason = 'invalid partner ID'
    elif not _valid_id(partner.get('zone')):
        reason = 'invalid partner zone'
    elif not _valid_time(order.get('prep_minutes')):
        reason = 'invalid preparation time'
    elif not _valid_time(partner.get('workload_minutes', 0)):
        reason = 'invalid workload time'
    elif not _valid_time(now):
        reason = 'invalid current time'
    else:
        reason = None

    if reason:
        return {
            'partner_id': partner.get('partner_id'),
            'eta_minutes': None,
            'eligible': False,
            'reason': reason
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

    pickup = now + leg1 + partner.get('workload_minutes', 0)

    eta = pickup + order['prep_minutes'] + leg2

    return {
        'partner_id': partner['partner_id'],
        'pickup_minutes': pickup,
        'eta_minutes': eta,
        'eligible': True,
        'reason': 'eligible'
    }


def assign_order(order, partners, travel, now=0):
    return {
        'order_id': order.get('order_id') if isinstance(order, dict) else None,
        'partner_id': None,
        'pickup_minutes': None,
        'eta_minutes': None,
        'reason': 'assignment logic pending'
    }


def process_cancellation(partner, order_id, event_id):
    return deepcopy(partner)
