"""This file implements FuzzyWOfS, a fuzzy variation of the
Water Observations from Space decision tree classifier
(Mueller+17).

Exports `wofs`, a classifier with a `predict` and
`fuzzy_predict` method.
"""

from graphviz import Digraph
import numpy as np
import scipy.special

class FuzzyWOfSLeaf:
    """A leaf node of the FuzzyWOfS classifier."""
    
    # Current leaf index.
    LEAF_ID = 0

    def __init__(self, wet_prob, n_wet, n_dry=None):
        """Initialise the leaf node.
        
        Parameters
        ----------
        wet_prob : float in [0, 1]
            Probability that a pixel at this leaf node is wet.
        
        n_wet : int
            Number of wet pixels in the training set (if n_dry)
            OR
            Number of total pixels in the training set (if not n_dry).
        
        n_dry : int
            Optional. Number of dry pixels in the training set.
        """
        self.wet_prob = wet_prob
        self.id = FuzzyWOfSLeaf.LEAF_ID
        FuzzyWOfSLeaf.LEAF_ID += 1
        if n_dry is not None:
            self.n_wet = n_wet
            self.n_dry = n_dry
        else:
            self.n_wet = int(n_wet * wet_prob)
            self.n_dry = n_wet - self.n_wet
        self.colour = 'blue' if wet_prob > 0.5 else 'red'
    
    def __repr__(self):
        return f'FuzzyWOfSLeaf({self.wet_prob}, {self.n_wet}, {self.n_dry})'
    
    def __str__(self):
        """Get a string representation of the leaf node."""
        return f'p(wet={self.wet_prob:.02f})'
    
    def predict(self, values) -> bool:
        """Predict whether a pixel is wet or dry.
        
        Parameters
        ----------
        values : (6, ...) array of floats
            Array of pixel values.
        
        Returns
        -------
        bool
        """
        return self._predict(values)
    
    def _predict(self, values):
        """Predict whether a pixel is wet or dry (given band indices and reflectances).
        
        values : (9, ...) array of floats
            Array of band index and pixel values.
        """
        return self.wet_prob > 0.5
    
    def fuzzy_predict(self, means, stdevs, hard_edges=False) -> float:
        """Predict the probability that a pixel is wet.
        
        Parameters
        ----------
        means : (6, ...) array of floats
            Array of pixel values.
        
        stdevs : (6, ...) array of floats
            Array of uncertainties in pixel values.
        
        hard_edges : bool
            Whether the prediction should be hard rather than fuzzy.
            Default False.
        
        Returns
        -------
        float
        """
        return self._fuzzy_predict(means, stdevs, hard_edges=hard_edges)
    
    def _fuzzy_predict(self, means, stdevs, hard_edges=False) -> float:
        """Predict the probability that a pixel is wet (given band indices and values).
        
        Parameters
        ----------
        means : (9, ...) array of floats
            Array of band indices and pixel values.
        
        stdevs : (9, ...) array of floats
            Array of uncertainties in band indices and pixel values.
        
        hard_edges : bool
            Whether the prediction should be hard rather than fuzzy.
            Default False.
        
        Returns
        -------
        float
        """
        if not hard_edges:
            return self.wet_prob
        return self.wet_prob > 0.5
    
    def to_string(self) -> str:
        """Convert this node to a string to represent the FuzzyWOfS equation."""
        return f'{self.wet_prob:.02f}'
    
    def count(self) -> (int, int):
        """Count how many pixels are wet and dry in this node.
        
        Returns
        -------
        (int, int)
            (n wet, n dry)
        """
        return self.n_wet, self.n_dry
    
    def get_leaf(self, values) -> int:
        """Get the leaf node classifying a pixel.
        
        Parameters
        ----------
        values : (6, ...) array of floats
            Array of pixel values.
        
        Returns
        -------
        int
            Leaf ID.
        """
        return self._get_leaf(values)
    
    def _get_leaf(self, values) -> int:
        """Get the leaf node classifying a pixel (given band indices and values).
        
        Parameters
        ----------
        values : (9, ...) array of floats
            Array of band indices and pixel values.
        
        Returns
        -------
        int
            Leaf ID.
        """
        return self.id
    
    def get_fuzzy_leaf(self, means, stdevs, hard_edges=False) -> int:
        """Get the leaf nodes classifying a pixel.
        
        Parameters
        ----------
        means : (6, ...) array of floats
            Array of band indices and pixel values.
        
        stdevs : (6, ...) array of floats
            Array of uncertainties in band indices and pixel values.
        
        hard_edges : bool
            Whether the prediction should be hard rather than fuzzy.
            Default False.
        
        Returns
        -------
        [float]
            Percentage membership to each leaf ID.
        """
        return _get_fuzzy_leaf(means, stdevs, hard_edges=hard_edges)
    
    def _get_fuzzy_leaf(self, means, stdevs, hard_edges=False) -> int:
        """Get the leaf nodes classifying a pixel (given band indices and values).
        
        Parameters
        ----------
        means : (9, ...) array of floats
            Array of band indices and pixel values.
        
        stdevs : (9, ...) array of floats
            Array of uncertainties in band indices and pixel values.
        
        hard_edges : bool
            Whether the prediction should be hard rather than fuzzy.
            Default False.
        
        Returns
        -------
        int
            Leaf ID.
        """
        membership = np.zeros((23,) + means.shape[1:])
        membership[self.id] = 1
        return membership
    
    def name(self) -> str:
        """Get the name of this node."""
        confidence = self.wet_prob if self.wet_prob > 0.5 else 1 - self.wet_prob
        return f'LEAF {self.id}\n{confidence:.02%}'
    
    def build_graphviz(self, dot) -> Digraph:
        """Build a GraphViz representation of the tree."""
        return dot
    
    
class FuzzyWOfSNode:
    """An internal node of the FuzzyWOfS classifier."""
    
    # Map measurement names to list indices.
    MEASUREMENTS = {
        'tm1': 0,
        'tm2': 1,
        'tm3': 2,
        'tm4': 3,
        'tm5': 4,
        'tm7': 5,
        'ndi52': 6,
        'ndi43': 7,
        'ndi72': 8,
    }
    
    # List of measurement names in order of list index.
    MEASUREMENT_NAMES = [
        'tm1',
        'tm2',
        'tm3',
        'tm4',
        'tm5',
        'tm7',
        'ndi52',
        'ndi43',
        'ndi72',
    ]
    
    # Current node index.
    NODE_ID = 0
    
    @staticmethod
    def band_ratio(a, b) -> float:
        """
        Calculates a normalised ratio index between bands a and b.
        """
        c = (a - b) / (a + b)
        return c
    
    @staticmethod
    def band_ratio_sigma(a, b, a_sigma, b_sigma) -> float:
        """
        Calculates the uncertainty in normalised ratio index between bands a and b.
        """
        # The band ratio uncertainty is numerically unstable, so let's stabilise it.
        # (a - b) / (a + b) = a / (a + b) - b / (a + b)
        # Propagate through (a + b):
        denominator = a + b
        denominator_sigma = np.hypot(a, b)
        # Propagate through a / (a + b):
        c = a / denominator
        c_sigma = np.abs(c) * np.sqrt((a / a_sigma) ** 2 + (denominator / denominator_sigma) ** 2)
        # And b / (a + b):
        d = b / denominator
        d_sigma = np.abs(d) * np.sqrt((b / b_sigma) ** 2 + (denominator / denominator_sigma) ** 2)
        # Then propagate the sum:
        return np.hypot(c, d)
    
    @staticmethod
    def landsat_values(px) -> [float]:
        """Convert Landsat pixel values into band ratios and pixel values.
        
        Parameters
        ----------
        px : (6, ...) array of floats
            Bands 1-5 and 7 of Landsat.
            
        Returns
        -------
        (9, ...) array of floats
            Bands 1-5 and 7 of Landsat, plus NDI 52, 43, and 72.
        """
        ndi_52 = FuzzyWOfSNode.band_ratio(px[4], px[1])
        ndi_43 = FuzzyWOfSNode.band_ratio(px[3], px[2])
        ndi_72 = FuzzyWOfSNode.band_ratio(px[5], px[1])

        b1 = px[0]
        b2 = px[1]
        b3 = px[2]
        b4 = px[3]
        b5 = px[4]
        b7 = px[5]
        
        return np.stack([b1, b2, b3, b4, b5, b7, ndi_52, ndi_43, ndi_72])
    
    @staticmethod
    def landsat_values_sigma(means, sigmas) -> [float]:
        """Convert Landsat pixel uncertainties into band ratio and pixel uncertainties.
        
        Parameters
        ----------
        means : (6, ...) array of floats
            Bands 1-5 and 7 of Landsat.
        sigmas : (6, ...) array of floats
            Uncertainty in bands 1-5 and 7 of Landsat.
            
        Returns
        -------
        (9, ...) array of floats
            Uncertainty of bands 1-5 and 7 of Landsat, plus NDI 52, 43, and 72.
        """
        ndi_52_sigma = FuzzyWOfSNode.band_ratio_sigma(means[4], means[1], sigmas[4], sigmas[1])
        ndi_43_sigma = FuzzyWOfSNode.band_ratio_sigma(means[3], means[2], sigmas[3], sigmas[2])
        ndi_72_sigma = FuzzyWOfSNode.band_ratio_sigma(means[5], means[1], sigmas[5], sigmas[1])

        b1_sigma = np.tile(sigmas[0], means.shape[1:])
        b2_sigma = np.tile(sigmas[1], means.shape[1:])
        b3_sigma = np.tile(sigmas[2], means.shape[1:])
        b4_sigma = np.tile(sigmas[3], means.shape[1:])
        b5_sigma = np.tile(sigmas[4], means.shape[1:])
        b7_sigma = np.tile(sigmas[5], means.shape[1:])
        
        return np.stack([b1_sigma, b2_sigma, b3_sigma, b4_sigma, b5_sigma,
                         b7_sigma, ndi_52_sigma, ndi_43_sigma, ndi_72_sigma])

    def __init__(self, split_feature, split_value, left_child, right_child):
        """Initialise the node.
        
        Parameters
        ----------
        split_feature : str
            Feature to split on; one of FuzzyWOfSNode.MEASUREMENT_NAMES.
            
        split_value : float
            Value of the feature to split on.
        
        left_child : FuzzyWOfSNode or FuzzyWOfSLeaf
            Node for split_feature <= split_value.
        
        right_child : FuzzyWOfSNode or FuzzyWOfSLeaf
            Node for split_feature > split_value.
        """
        self.left_child = left_child
        self.right_child = right_child
        self.split_feature = split_feature
        self.split_value = split_value
        self.split_index = self.MEASUREMENTS[self.split_feature]
        self.id = FuzzyWOfSNode.NODE_ID
        FuzzyWOfSNode.NODE_ID += 1
        self.colour = 'white'
    
    def __repr__(self):
        return f'FuzzyWOfSNode({self.split_feature}, {self.split_value}, {self.left_child}, {self.right_child})'
    
    def predict(self, values):
        """Predict whether a pixel is wet or dry.
        
        Parameters
        ----------
        values : (6, ...) array of floats
            Array of pixel values.
        
        Returns
        -------
        bool
        """
        values = self.landsat_values(values)
        return self._predict(values)
    
    def _predict(self, values):
        """Predict whether a pixel is wet or dry (given band indices and pixels).
        
        Parameters
        ----------
        values : (9, ...) array of floats
            Array of band indices and pixel values.
        
        Returns
        -------
        bool
        """
        left = self.left_child._predict(values)
        right = self.right_child._predict(values)
        return np.where(values[self.split_index] <= self.split_value,
                        left,
                        right)
    
    def fuzzy_predict(self, means, stdevs, hard_edges=False):
        """Predict the probability that a pixel is wet.
        
        Parameters
        ----------
        means : (6, ...) array of floats
            Array of pixel values.
        
        stdevs : (6, ...) array of floats
            Array of uncertainties in pixel values.
        
        hard_edges : bool
            Whether the prediction should be hard rather than fuzzy.
            Default False.
        
        Returns
        -------
        float
        """
        means = self.landsat_values(means)
        stdevs = self.landsat_values_sigma(means, stdevs)
        return self._fuzzy_predict(means, stdevs, hard_edges=hard_edges)
    
    def _fuzzy_predict(self, means, stdevs, hard_edges=False):
        """Predict the probability that a pixel is wet (given band indices and values).
        
        Parameters
        ----------
        means : (9, ...) array of floats
            Array of band indices and pixel values.
        
        stdevs : (9, ...) array of floats
            Array of uncertainties in band indices and pixel values.
        
        hard_edges : bool
            Whether the prediction should be hard rather than fuzzy.
            Default False.
        
        Returns
        -------
        float
        """
        left = self.left_child._fuzzy_predict(means, stdevs, hard_edges=hard_edges)
        right = self.right_child._fuzzy_predict(means, stdevs, hard_edges=hard_edges)
        mean = means[self.split_index]
        stdev = stdevs[self.split_index]
        
        # How much of the Gaussian goes into the left subtree?
        # Integrate G(x) from -inf to split value.
        weight = scipy.special.erf((mean - self.split_value) / stdev)
        # If the split value is much greater than the mean, then we almost surely go down the left tree.
        # The weight becomes -1.
        # Conversely, if the split value is much much less than the mean, then we almost surely go down the right tree.
        # The weight becomes 1.
        # If we add 1 and halve, our numbers map from 0 (all left) to 1 (all right).
        weight = (weight + 1) / 2
        if hard_edges:
            weight = (mean - self.split_value) / stdev > 0
        return left * (1 - weight) + right * weight
    
    def to_string(self):
        """Convert this node to a string to represent the FuzzyWOfS equation."""
        means = [f'mu_{m}' for m in self.MEASUREMENT_NAMES]
        stdevs = [f'sigma_{m}' for m in self.MEASUREMENT_NAMES]
    
        left = self.left_child.to_string()
        right = self.right_child.to_string()

        mean = means[self.split_index]
        stdev = stdevs[self.split_index]
        
        weight = f'(erf(({mean} - {self.split_value}) / {stdev}) + 1) / 2'
        return f'({left}) * (1 - {weight}) + ({right}) * {weight}'
    
    def count(self):
        """Count how many pixels are wet and dry in all children of this node.
        
        Returns
        -------
        (int, int)
            (n wet, n dry)
        """
        if hasattr(self, '_count'):
            return self._count
        lw, ld = self.left_child.count()
        rw, rd = self.right_child.count()
        self._count = (lw + rw, ld + rd)
        return (lw + rw, ld + rd)
    
    def get_leaf(self, values):
        """Get the leaf node classifying a pixel.
        
        Parameters
        ----------
        values : (6, ...) array of floats
            Array of pixel values.
        
        Returns
        -------
        int
            Leaf ID.
        """
        values = self.landsat_values(values)
        return self._get_leaf(values)
    
    def _get_leaf(self, values):
        """Get the leaf node classifying a pixel (given band indices and values).
        
        Parameters
        ----------
        values : (9, ...) array of floats
            Array of band indices and pixel values.
        
        Returns
        -------
        int
            Leaf ID.
        """
        left = self.left_child._get_leaf(values)
        right = self.right_child._get_leaf(values)
        return np.where(values[self.split_index] <= self.split_value,
                        left,
                        right)
    
    def get_fuzzy_leaf(self, means, stdevs, hard_edges=False):
        """Get the leaf nodes classifying a pixel.
        
        Parameters
        ----------
        means : (6, ...) array of floats
            Array of pixel values.
        
        stdevs : (6, ...) array of floats
            Array of uncertainties in pixel values.
        
        hard_edges : bool
            Whether the prediction should be hard rather than fuzzy.
            Default False.
        
        Returns
        -------
        [float]
            Array of memberships for each leaf.
        """
        means = self.landsat_values(means)
        stdevs = self.landsat_values_sigma(means, stdevs)
        return self._get_fuzzy_leaf(means, stdevs, hard_edges=hard_edges)
    
    def _get_fuzzy_leaf(self, means, stdevs, hard_edges=False):
        """Get the leaf nodes classifying a pixel (given band indices and values).
        
        Parameters
        ----------
        means : (9, ...) array of floats
            Array of band indices and pixel values.
        
        stdevs : (9, ...) array of floats
            Array of uncertainties in band indices and pixel values.
        
        hard_edges : bool
            Whether the prediction should be hard rather than fuzzy.
            Default False.
        
        Returns
        -------
        [float]
            Array of memberships for each leaf.
        """
        left = self.left_child._get_fuzzy_leaf(means, stdevs, hard_edges=hard_edges)
        right = self.right_child._get_fuzzy_leaf(means, stdevs, hard_edges=hard_edges)
        mean = means[self.split_index]
        stdev = stdevs[self.split_index]
        
        # How much of the Gaussian goes into the left subtree?
        # Integrate G(x) from -inf to split value.
        weight = scipy.special.erf((mean - self.split_value) / stdev)
        # If the split value is much greater than the mean, then we almost surely go down the left tree.
        # The weight becomes -1.
        # Conversely, if the split value is much much less than the mean, then we almost surely go down the right tree.
        # The weight becomes 1.
        # If we add 1 and halve, our numbers map from 0 (all left) to 1 (all right).
        weight = (weight + 1) / 2
        if hard_edges:
            weight = (mean - self.split_value) / stdev > 0
        return left * (1 - weight) + right * weight
    
    def name(self):
        """Get the name of this node."""
        return f'NODE {self.id} n={self.count()}'
    
    def build_graphviz(self, dot=None):
        """Build a GraphViz representation of the tree."""
        if dot is None:
            dot = Digraph()

        # Make left child.
        dot.node(name=self.left_child.name(), label=self.left_child.name(), color=self.left_child.colour)
        dot.edge(self.name(), self.left_child.name())
        self.left_child.build_graphviz(dot)

        # Make right child.
        node = dot.node(name=self.right_child.name(), label=self.right_child.name(), color=self.right_child.colour)
        dot.edge(self.name(), self.right_child.name())
        self.right_child.build_graphviz(dot)
        
        return dot


def _get_wofs():
    Leaf = FuzzyWOfSLeaf
    Node = FuzzyWOfSNode

    # Left subtree.
    left = Node('tm1', 2083.5,
               Node('tm7', 323.5,
                   Node('ndi43', 0.61,
                        Leaf(0.972, 44615),
                        Leaf(0.000, 173)),
                   Node('tm1', 1400.5,
                        Node('ndi72', -0.23,
                             Node('ndi43', 0.22,
                                  Leaf(0.786, 5264),
                                  Node('tm1', 473.0,
                                       Leaf(0.978, 360),
                                       Leaf(1 - 0.967, 869))),
                             Node('tm1', 379.0,
                                  Leaf(0.831, 160),
                                  Leaf(1 - 0.988, 1954))),
                       Node('ndi43', -0.01,
                            Leaf(0.977, 257),
                            Leaf(0.003, 2810)))),
               Leaf(0.001, 6683))

    # Right subtree.
    right = Node('ndi52', 0.23,
                 Node('tm1', 334.5,
                      Node('ndi43', 0.54,
                           Node('ndi52', 0.12,  # Typo in the paper here.
                                Leaf(0.801, 2467),
                                Node('tm3', 364.5,
                                     Node('tm1', 129.5,
                                          Leaf(0.632, 484),
                                          Leaf(1 - 0.902, 1727)),
                                     Node('tm1', 300.5,
                                          Leaf(0.757, 889),
                                          Leaf(1 - 0.885, 358)))),
                           Leaf(1 - 0.974, 4503)),
                      Leaf(1 - 0.981, 12441)),
                 Node('ndi52', 0.34,
                      Node('tm1', 249.5,
                           Node('ndi43', 0.45,
                                Node('tm3', 364.5,
                                     Node('tm1', 129.5,
                                          Leaf(0.616, 185),
                                          Leaf(1 - 0.940, 1072)),
                                     Leaf(0.584, 620)),
                                Leaf(1 - 0.979, 5703)),
                           Leaf(1 - 0.984, 10034)),
                      Leaf(1 - 0.996, 80246)))

    # All together:
    wofs_tree = Node('ndi52', -0.01, left, right)
    return wofs_tree


def guess_noise(values, p=0.11):
    """Guess per-band noise as a percentage of the median values.
    
    Parameters
    ----------
    values : (n, ...) array of floats
    p : float
        Noise percentage. Optional; default 0.11.
    
    Returns
    -------
    (n,) array of floats
    """
    return np.abs(np.median(
        values, axis=tuple(range(1, values.ndim)))) * p


wofs = _get_wofs()
