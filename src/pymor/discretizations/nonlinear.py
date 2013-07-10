# -*- coding: utf-8 -*-
# This file is part of the pyMor project (http://www.pymor.org).
# Copyright Holders: Felix Albrecht, Rene Milk, Stephan Rave
# License: BSD 2-Clause License (http://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

import numpy as np

from pymor.algorithms.timestepping import explicit_euler
from pymor.la.interfaces import VectorArrayInterface
from pymor.tools import dict_property, selfless_arguments
from pymor.operators import OperatorInterface, LinearOperatorInterface, ConstantOperator
from pymor.discretizations.interfaces import DiscretizationInterface


class InstationaryNonlinearDiscretization(DiscretizationInterface):

    operator = dict_property('operators', 'operator')
    rhs = dict_property('operators', 'rhs')
    initial_data = dict_property('operators', 'initial_data')

    _logging_disabled = False
    @property
    def logging_disabled(self):
        return self._logging_disabled

    def __init__(self, operator, rhs, initial_data, T, nt, parameter_space=None, visualizer=None, name=None):
        assert isinstance(operator, OperatorInterface)
        assert isinstance(rhs, LinearOperatorInterface)
        assert isinstance(initial_data, (VectorArrayInterface, OperatorInterface))
        assert not isinstance(initial_data, OperatorInterface) or initial_data.dim_source == 0
        if isinstance(initial_data, VectorArrayInterface):
            initial_data = ConstantOperator(initial_data, name='initial_data')
        assert operator.dim_source == operator.dim_range == rhs.dim_source == initial_data.dim_range
        assert rhs.dim_range == 1

        super(InstationaryNonlinearDiscretization, self).__init__()
        self.operators = {'operator': operator, 'rhs': rhs, 'initial_data': initial_data}
        self.build_parameter_type(inherits={'operator': operator, 'rhs': rhs, 'initial_data': initial_data},
                                  provides={'_t': 0})
        self.T = T
        self.nt = nt
        self.parameter_space = parameter_space

        if visualizer is not None:
            self.visualize = visualizer

        self.solution_dim = operator.dim_range
        self.name = name
        self.lock()

    with_arguments = set(selfless_arguments(__init__)).union(['operators'])

    def with_(self, **kwargs):
        assert 'operators' not in kwargs or 'rhs' not in kwargs and 'operator' not in kwargs
        assert 'operators' not in kwargs or set(kwargs['operators'].keys()) <= set(('operator', 'rhs'))

        if not 'visualizer' in kwargs:
            kwargs['visualizer'] = self.visualize if hasattr(self, 'visualize') else None
        if 'operators' in kwargs:
            kwargs.update(kwargs.pop('operators'))

        return self._with_via_init(kwargs)

    def _solve(self, mu=None):
        if not self._logging_disabled:
            self.logger.info('Solving {} for {} ...'.format(self.name, mu))
        mu_A = self.map_parameter(mu, 'operator', provide={'_t': np.array(0)})
        mu_F = self.map_parameter(mu, 'rhs', provide={'_t': np.array(0)})
        U0 = self.initial_data.apply(0, self.map_parameter(mu, 'initial_data'))
        return explicit_euler(self.operator, self.rhs, U0, 0, self.T, self.nt, mu_A, mu_F)

    def disable_logging(self, doit=True):
        self._logging_disabled = doit

    def enable_logging(self, doit=True):
        self._logging_disabled = not doit
