# ==================================================================
# File: bridge_app/controllers/__init__.py
# Description: Controller package initialization.
#
# Copyright (C) 2026 Arean Narrayan - SynoraStudio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==================================================================

from .ui_controller import ui_bp
from .engine_controller import api_bp
from .observability_controller import obs_bp
from .health_controller import health_bp

# Register all routes on api_bp
from . import template_controller
from . import job_controller
from . import connection_controller
from . import pull_controller
