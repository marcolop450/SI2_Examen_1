import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PagoService } from '../../core/services/pago';

@Component({
  selector: 'app-cu14-comisiones',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cu14-comisiones.html',
  styleUrls: ['./cu14-comisiones.css']
})
export class Cu14ComisionesComponent implements OnInit {
  pagos: any[] = [];
  cargando: boolean = true;

  constructor(private pagoService: PagoService) {}

  ngOnInit(): void {
    this.cargarComisiones();
  }

  cargarComisiones(): void {
    this.cargando = true;
    this.pagoService.obtenerPagos().subscribe({
      next: (data) => {
        this.pagos = data;
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar comisiones:', err);
        this.cargando = false;
      }
    });
  }

  // Calculamos los totales leyendo lo que calculó la Base de Datos
  get totalComisiones(): number {
    return this.pagos.reduce((acc, pago) => acc + parseFloat(pago.comision_plataforma_decimal), 0);
  }

  get totalCobrado(): number {
    return this.pagos.reduce((acc, pago) => acc + parseFloat(pago.monto_total_decimal), 0);
  }
}
