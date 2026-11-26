"""Native PyTorch periodic full-complex STFT operator (CPU/CUDA).

Provides a unified tensor operator for all Griffin-Lim solvers, online
Rayleigh-Ritz estimation, and checkpoint safeguarding.
"""
from __future__ import annotations
import numpy as np


def _torch():
    try:
        import torch
    except ImportError as e:
        raise ImportError('Install PyTorch from official instructions for your CUDA version') from e
    return torch


class TorchPeriodicSTFT:
    def __init__(self,N,window,hop,n_fft,device='cpu',dtype='complex128'):
        torch=_torch()
        if N%hop:raise ValueError('N must be divisible by hop')
        if n_fft<len(window):raise ValueError('n_fft >= window')
        self.device=device;self.N=N;self.W=len(window);self.hop=hop;self.n_fft=n_fft
        self.dtype=torch.complex128 if dtype=='complex128' else torch.complex64
        self.rdtype=torch.float64 if dtype=='complex128' else torch.float32
        self.window=torch.as_tensor(window,device=device,dtype=self.rdtype)
        self.index=(torch.arange(N//hop,device=device)[:,None]*hop+torch.arange(self.W,device=device)[None,:])%N
        self.M=(N//hop)*n_fft
        flat=self.index.reshape(-1)
        diag=torch.zeros(N,device=device,dtype=self.rdtype)
        diag.scatter_add_(0,flat,n_fft*(self.window*self.window).repeat(N//hop))
        if float(diag.min())<=1e-14:raise ValueError('singular frame operator')
        self.frame_diag=diag; self.projections=0

    def tensor(self,z):
        torch=_torch()
        return torch.as_tensor(z,device=self.device,dtype=self.dtype)

    def analyze(self,x):
        torch=_torch()
        x=self.tensor(x)
        if x.ndim!=1:raise ValueError('single input signal required')
        frames=x[self.index]*self.window
        if self.n_fft>self.W:
            frames=torch.nn.functional.pad(frames,(0,self.n_fft-self.W))
        return torch.fft.fft(frames,dim=-1).reshape(-1)

    def adjoint(self,c):
        torch=_torch()
        c=self.tensor(c).reshape(-1,self.n_fft)
        frames=torch.fft.ifft(c,dim=-1)*self.n_fft
        out=torch.zeros(self.N,device=self.device,dtype=self.dtype)
        out.scatter_add_(0,self.index.reshape(-1),
                         (frames[:,:self.W]*self.window).reshape(-1))
        return out

    def synthesize(self,c):
        return self.adjoint(c)/self.frame_diag

    def project_range(self,c):
        self.projections+=1
        return self.analyze(self.synthesize(c))

    def G(self,c,s):
        torch=_torch();mag=torch.abs(c)
        # Exact zero-phase fallback: s_i * 1 rather than NaNs.
        phase=torch.where(mag>0,c/torch.where(mag>0,mag,torch.ones_like(mag)),torch.ones_like(c))
        return self.project_range(s*phase)

    def synchronize(self):
        torch=_torch()
        if self.device.startswith('cuda'):torch.cuda.synchronize(self.device)


