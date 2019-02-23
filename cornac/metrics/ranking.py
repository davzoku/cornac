# -*- coding: utf-8 -*-

"""
@author: Aghiles Salah
         Quoc-Tuan Truong <tuantq.vnu@gmail.com>
"""

import numpy as np


class RankingMetric:
    """Ranking Metric.

    Attributes
    ----------
    type: string, value: 'ranking'
        Type of the metric, e.g., "ranking", "rating".

    name: string, default: None
        Name of the measure.

    k: int, optional, default: -1 (all)
        The number of items in the top@k list.
        If None, all items will be considered.

    """

    def __init__(self, name=None, k=-1):
        self.type = 'ranking'
        self.name = name
        self.k = k

    def compute(self, **kwargs):
        raise NotImplementedError()


class NDCG(RankingMetric):
    """Normalized Discount Cumulative Gain.

    Parameters
    ----------
    k: int, optional, default: -1 (all)
        The number of items in the top@k list.
        If None, all items will be considered.

    References
    ----------
    https://en.wikipedia.org/wiki/Discounted_cumulative_gain

    """

    def __init__(self, k=-1):
        RankingMetric.__init__(self, name='NDCG@{}'.format(k), k=k)

    @staticmethod
    def dcg_score(gt_pos, pd_rank, k=-1):
        """Compute Discounted Cumulative Gain score.

        Parameters
        ----------
        gt_pos: Numpy array
            Binary vector of positive items.

        pd_rank: Numpy array
            Item ranking prediction.

        k: int, optional, default: -1 (all)
            The number of items in the top@k list.
            If None, all items will be considered.

        Returns
        -------
        dcg: A scalar
            Discounted Cumulative Gain score.

        """
        if k > 0:
            pd_rank = pd_rank[:k]

        gt_pos = np.take(gt_pos, pd_rank)
        gain = 2 ** gt_pos - 1
        discounts = np.log2(np.arange(len(gt_pos)) + 2)

        return np.sum(gain / discounts)

    def compute(self, gt_pos, pd_rank, **kwargs):
        """Compute Normalized Discounted Cumulative Gain score.

        Parameters
        ----------
        gt_pos: Numpy array
            Binary vector of positive items.

        pd_rank: Numpy array
            Item ranking prediction.

        **kwargs: For compatibility

        Returns
        -------
        ndcg: A scalar
            Normalized Discounted Cumulative Gain score.

        """
        dcg = self.dcg_score(gt_pos, pd_rank, self.k)
        idcg = self.dcg_score(gt_pos, np.argsort(gt_pos)[::-1], self.k)
        ndcg = dcg / idcg

        return ndcg


class NCRR(RankingMetric):
    """Normalized Cumulative Reciprocal Rank.

    Parameters
    ----------
    k: int, optional, default: -1 (all)
        The number of items in the top@k list.
        If None, all items will be considered.

    """

    def __init__(self, k=-1):
        RankingMetric.__init__(self, name='NCRR@{}'.format(k), k=k)

    def compute(self, gt_pos, pd_rank, **kwargs):
        """Compute Normalized Cumulative Reciprocal Rank score.

        Parameters
        ----------
        gt_pos: Numpy array
            Binary vector of positive items.

        pd_rank: Numpy array
            Item ranking prediction.

        **kwargs: For compatibility

        Returns
        -------
        ncrr: A scalar
            Normalized Cumulative Reciprocal Rank score.

        """
        gt_pos_items = np.nonzero(gt_pos > 0)

        # Compute Ideal CRR
        ideal_rank = np.arange(len(gt_pos_items[0]))
        ideal_rank = ideal_rank + 1  # +1 because indices starts from 0 in python
        icrr = np.sum(1. / ideal_rank)

        # Compute CRR
        rec_rank = np.where(np.in1d(pd_rank, gt_pos_items))[0]
        rec_rank = rec_rank + 1  # +1 because indices starts from 0 in python
        crr = np.sum(1. / rec_rank)

        # Compute nDCG
        ncrr_i = crr / icrr

        return ncrr_i


class MRR(RankingMetric):
    """Mean Reciprocal Rank.

    Parameters
    ----------
    k: int, optional, default: -1 (all)
        The number of items in the top@k list.
        If None, all items will be considered.

    References
    ----------
    https://en.wikipedia.org/wiki/Mean_reciprocal_rank
    """

    def __init__(self):
        RankingMetric.__init__(self, name='MRR')


    def compute(self, gt_pos, pd_rank, **kwargs):
        """Compute Mean Reciprocal Rank score.

        Parameters
        ----------
        gt_pos: Numpy array
            Binary vector of positive items.

        pd_rank: Numpy array
            Item ranking prediction.

        **kwargs: For compatibility

        Returns
        -------
        mrr: A scalar
            Mean Reciprocal Rank score.

        """
        gt_pos_items = np.nonzero(gt_pos > 0)
        matched_items = np.nonzero(np.in1d(pd_rank, gt_pos_items))[0]

        if len(matched_items) == 0:
            raise ValueError('No matched between ground-truth items and recommendations')

        mrr = np.divide(1, (matched_items[0] + 1))  # +1 because indices start from 0 in python
        return mrr


class MeasureAtK(RankingMetric):
    """Measure at K.

    Attributes
    ----------
    k: int, optional, default: -1 (all)
        The number of items in the top@k list.
        If None, all items will be considered.

    """
    def __init__(self, name=None, k=-1):
        RankingMetric.__init__(self, name, k)

    def compute(self, gt_pos, pd_rank, **kwargs):
        """Compute TP, TP+FN, and TP+FP.

        Parameters
        ----------
        gt_pos: Numpy array
            Binary vector of positive items.

        pd_rank: Numpy array
            Item ranking prediction.

        **kwargs: For compatibility

        Returns
        -------
        tp: A scalar
            True positive.

        tp_fn: A scalar
            True positive + false negative.

        tp_fp: A scalar
            True positive + false positive.

        """
        if self.k > 0:
            pd_rank = pd_rank[:self.k]

        pred = np.zeros_like(gt_pos)
        pred[pd_rank] = 1

        tp = np.sum(pred * gt_pos)
        tp_fn = np.sum(gt_pos)
        tp_fp = np.sum(pred)

        return tp, tp_fn, tp_fp


class Precision(MeasureAtK):
    """Precision@K.

    Parameters
    ----------
    k: int, optional, default: -1 (all)
        The number of items in the top@k list.
        If None, all items will be considered.

    """

    def __init__(self, k=-1):
        super().__init__(name="Precision@{}".format(k), k=k)

    def compute(self, gt_pos, pd_rank, **kwargs):
        """Compute Precision score.

        Parameters
        ----------
        gt_pos: Numpy array
            Binary vector of positive items.

        pd_rank: Numpy array
            Item ranking prediction.

        **kwargs: For compatibility

        Returns
        -------
        res: A scalar
            Precision score.

        """
        tp, tp_fn, tp_fp = MeasureAtK.compute(self, gt_pos, pd_rank, **kwargs)
        return tp / tp_fp


class Recall(MeasureAtK):
    """Recall@K.

    Parameters
    ----------
    k: int, optional, default: -1 (all)
        The number of items in the top@k list.
        If None, all items will be considered.

    """

    def __init__(self, k=-1):
        super().__init__(name="Recall@{}".format(k), k=k)

    def compute(self, gt_pos, pd_rank, **kwargs):
        """Compute Recall score.

        Parameters
        ----------
        gt_pos: Numpy array
            Binary vector of positive items.

        pd_rank: Numpy array
            Item ranking prediction.

        **kwargs: For compatibility

        Returns
        -------
        res: A scalar
            Recall score.

        """
        tp, tp_fn, tp_fp = MeasureAtK.compute(self, gt_pos, pd_rank, **kwargs)
        return tp / tp_fn


class FMeasure(MeasureAtK):
    """F-measure@K@.

    Parameters
    ----------
    k: int, optional, default: -1 (all)
        The number of items in the top@k list.
        If None, all items will be considered.

    """

    def __init__(self, k=-1):
        super().__init__(name="F1@{}".format(k), k=k)

    def compute(self, gt_pos, pd_rank, **kwargs):
        """Compute F-Measure.

        Parameters
        ----------
        gt_pos: Numpy array
            Binary vector of positive items.

        pd_rank: Numpy array
            Item ranking prediction.

        **kwargs: For compatibility

        Returns
        -------
        res: A scalar
            F-Measure score.

        """
        tp, tp_fn, tp_fp = MeasureAtK.compute(self, gt_pos, pd_rank, **kwargs)

        prec = tp / tp_fp
        rec = tp / tp_fn
        if (prec + rec) > 0:
            f1 = 2 * (prec * rec) / (prec + rec)
        else:
            f1 = 0

        return f1


class AUC(RankingMetric):
    """Area Under the Curve (AUC).

    """

    def __init__(self):
        RankingMetric.__init__(self, name='AUC')

    def compute(self, pd_scores, gt_pos, gt_neg, **kwargs):
        """Compute Area Under the Curve (AUC).

        Parameters
        ----------
        pd_scores: Numpy array
            Prediction scores for items.

        gt_pos: Numpy array
            Binary vector of positive items.

        gt_neg: Numpy array
            Binary vector of negative items.

        **kwargs: For compatibility

        Returns
        -------
        res: A scalar
            AUC score.

        """
        pos_scores = pd_scores[gt_pos.astype(bool)]
        neg_scores = pd_scores[gt_neg.astype(bool)]

        auc = []
        for pos_score in pos_scores:
            auc.append(np.sum(pos_score > neg_scores) / len(neg_scores))

        return np.mean(auc)
