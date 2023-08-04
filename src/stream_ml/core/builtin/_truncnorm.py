"""Gaussian stream model."""

from __future__ import annotations

__all__: list[str] = []

from dataclasses import dataclass
from typing import TYPE_CHECKING

from stream_ml.core.builtin._norm import Normal
from stream_ml.core.builtin._stats.trunc_norm import logpdf
from stream_ml.core.builtin._utils import WhereRequiredError
from stream_ml.core.typing import Array, NNModel
from stream_ml.core.utils.compat import array_at

if TYPE_CHECKING:
    from stream_ml.core._data import Data
    from stream_ml.core.params import Params


@dataclass
class TruncatedNormal(Normal[Array, NNModel]):
    r"""Truncated Univariate Gaussian.

    In each dimension the background is a truncated normal distribution.

    Let :math:`\phi(x)` be the PDF of the normal distribution:

    .. math::

        \phi(x) = \frac{\exp{-((x - \mu)/\sigma)^2 / 2}}{\sqrt{2\pi} \sigma}

    The CDF :math:`\Phi(x)` is:

    .. math::

        \Phi(x) = \frac{1}{2} \text{erfc}\left(\frac{\mu - x}{\sigma \sqrt{2}}\right)

    The PDF of the truncated normal distribution is:

    .. math::

        f(x) = \frac{\phi(x)}{\Phi(b) - \Phi(a)}

    The model parameters are:

    - "mu" : mean
    - "ln-sigma" : log-standard deviation

    a, b are the lower and upper bounds of the distribution and are determined
    by the ``coord_bounds`` argument.

    Examples
    --------
    .. code-block:: python

        model = Normal(
            ...,
            coord_names=("x", "y"),  # independent coordinates
            coord_bounds={"x": (0, 1), "y": (1, 2)},
            params=ModelParameters(
                {
                    "x": {"slope": ModelParameter(...)},
                    "y": {"slope": ModelParameter(...)},
                }
            ),
        )
    """

    def ln_likelihood(
        self,
        mpars: Params[Array],
        /,
        data: Data[Array],
        *,
        where: Data[Array] | None = None,
        **kwargs: Array,
    ) -> Array:
        """Log-likelihood of the distribution.

        Parameters
        ----------
        mpars : Params[Array], positional-only
            Model parameters. Note that these are different from the ML
            parameters.
        data : Data[Array]
            Data (phi1, phi2).

        where : Data[Array], optional keyword-only
            Where to evaluate the log-likelihood. If not provided, then the
            log-likelihood is evaluated at all data points.
        **kwargs : Array
            Additional arguments.

        Returns
        -------
        Array
        """
        # 'where' is used to indicate which data points are available. If
        # 'where' is not provided, then all data points are assumed to be
        # available.
        if where is not None:
            idx = where[tuple(self.coord_bounds.keys())].array
        elif self.require_where:
            raise WhereRequiredError
        else:
            idx = self.xp.ones((len(data), self.ndim), dtype=bool)
            # This has shape (N,F) so will broadcast correctly.

        cns, cens = self.coord_names, self.coord_err_names
        x = data[cns].array

        a, b = self.xp.asarray([self.coord_bounds[k] for k in cns]).T[:, None, :]
        mu = self._stack_param(mpars, "mu", cns)[idx]
        ln_s = self._stack_param(mpars, "ln-sigma", cns)[idx]
        if cens is not None:
            # it's fine if sigma_o is 0
            sigma_o = data[cens].array[idx]
            ln_s = self.xp.logaddexp(2 * ln_s, 2 * self.xp.log(sigma_o)) / 2

        _0 = self.xp.zeros_like(x)
        value = logpdf(
            x[idx], loc=mu, ln_sigma=ln_s, a=(_0 + a)[idx], b=(_0 + b)[idx], xp=self.xp
        )

        lnliks = self.xp.full_like(x, 0)  # missing data is ignored
        lnliks = array_at(lnliks, idx).set(value)
        return lnliks.sum(1)  # (N,)
