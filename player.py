__author__ = 'colby'

import entity

PLAYER_SPEED = 64


Player = entity.EntityType(
	entity.RenderImage("pyramid_small.png"),
	entity.GridCollider(),
	lambda x, y: entity.PositionVelocity(x, y, 0, 0),
	lambda gui_cb: entity.Controllable(PLAYER_SPEED, gui_cb))
